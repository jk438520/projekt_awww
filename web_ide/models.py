import subprocess
from abc import abstractmethod

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import os


# Create your models here.

class FileSystemObject(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)
    creation_date = models.DateTimeField('date created', default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    availability = models.BooleanField(default=True)
    availability_change_date = models.DateTimeField('date of last availability change', blank=True, null=True)
    content_change_date = models.DateTimeField('date of last content change', default=timezone.now)
    parent_directory = models.ForeignKey('Directory', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    def children(self):
        return FileSystemObject.objects.filter(parent_directory=self, availability=True)

    def children_files(self):
        return File.objects.filter(parent_directory=self, availability=True)

    def children_directories(self):
        return Directory.objects.filter(parent_directory=self, availability=True)

    def delete(self, using=None, keep_parents=False):
        self.availability = False
        self.availability_change_date = timezone.now()
        self.save()
        for child in self.children():
            child.delete()

    @abstractmethod
    def is_directory(self):
        pass


class Directory(FileSystemObject):

    @classmethod
    def add_directory_in_root(cls, name, owner, description=""):
        if not FileSystemObject.objects.filter(
                availability=True,
                owner=owner,
                name=name,
                description=description,
                parent_directory=None).exists():
            new_directory = Directory(name=name, owner=owner, description=description)
            new_directory.save()
            return new_directory

    def add_directory(self, name, owner, description="", ):
        # ensure that the directory does not already exist
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                owner=owner,
                parent_directory=self).exists():
            new_directory = Directory(name=name, owner=owner, description=description, parent_directory=self)
            new_directory.save()
            return new_directory

    def add_file(self, name, owner, content="", description=""):
        # ensure that the file does not already exist
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                owner=owner,
                parent_directory=self).exists():
            new_file = File(
                name=name,
                owner=owner,
                description=description,
                content=content,
                parent_directory=self)
            new_file.save()
            return new_file

    def is_directory(self):
        return True


class File(FileSystemObject):
    content = models.TextField(blank=True, default='// this is content of file ' + str(super))
    compiled_content = models.TextField(blank=True, default='// this is compiled content of file ' + str(super))

    @classmethod
    def add_file_in_root(cls, name, owner, content="", description=""):
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                owner=owner,
                parent_directory=None).exists():
            new_file = File(name=name, owner=owner, content=content, description=description)
            new_file.save()
            return new_file

    def section_content(self):
        if self.content == "" or self.content is None:
            return
        for section in FileSection.objects.filter(file=self):
            section.delete()
        begin = 0
        end = 0
        cnt = 0
        for line in self.content.splitlines(True):
            cnt_b = line.count('{')
            cnt_e = line.count('}')
            cnt = cnt + cnt_b - cnt_e
            if cnt_e > 0 and cnt == 0:
                FileSection.objects.create(file=self, begin=begin, end=end).save()
                begin = end + 1
            end += 1
        if begin != end:
            FileSection.objects.create(file=self, begin=begin, end=end-1).save()

        return

    def is_directory(self):
        return False

    def compile(self, standard, optimization, processor):
        # put content into file
        with open("source_code.c", "w") as source_code:
            source_code.write(self.content)
            source_code.close()
            # compile file using sdcc
            sp = subprocess.Popen(["sdcc", "-S",
                                   "source_code.c",
                                   "-o", "compiled_code",
                                   processor,
                                   standard,
                                   optimization], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            sp.wait()
            if sp.returncode == 0:
                # read compiled file
                with open("compiled_code", "r") as compiled_code:
                    self.compiled_content = compiled_code.read()
                    compiled_code.close()
                    os.remove("compiled_code")
            else:
                self.compiled_content = sp.stderr.read().decode("utf-8")
            os.remove("source_code.c")
        self.save()
        return

    def get_streamified_compiled_content(self):
        acc = ''
        cnt_lines = 0
        for line in self.compiled_content.splitlines(True):
            if line == ';--------------------------------------------------------\n':
                if cnt_lines == 2:
                    yield acc
                    acc = ''
                    cnt_lines = 0
                cnt_lines += 1
            acc += line
        yield acc

    def get_content_by_section(self):
        sections = FileSection.objects.filter(file=self)
        if sections.count() == 0:
            return [self.content]
        index = 0
        lines = self.content.splitlines(True)
        acc = ''
        ret = []
        for line, li in zip(lines, range(len(lines))):
            if li == 0 or index >= sections.count():
                acc += line
                continue
            if li == sections[index].begin:
                ret.append(acc)
                acc = ''
            acc += line
            if li == sections[index].end:
                index += 1
                ret.append(acc)
                acc = ''
        if acc != '':
            ret.append(acc)
        return ret

    def __str__(self):
        return self.name


class FileSection(models.Model):
    name = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    creation_date = models.DateTimeField('date created', default=timezone.now)
    begin = models.IntegerField()
    end = models.IntegerField()

    file = models.ForeignKey('File', on_delete=models.CASCADE)

    def __str__(self):
        return "file: "+str(self.file)+" section: "+str(self.begin)+"-"+str(self.end)

class FileSectionType(models.Model):
    TYPE_CHOICES = [
        ('PROC', 'procedure'),
        ('COMM', 'comment'),
        ('COMP_DIR', 'compiler directive'),
        ('VAR_DEC', 'variable declaration'),
        ('ASM_CODE', 'assembly code'),
    ]
    type = models.CharField(max_length=200, choices=TYPE_CHOICES)
    section = models.ForeignKey('FileSection', on_delete=models.CASCADE)


class FileSectionStatus(models.Model):
    STATUS_CHOICES = [
        ('C', 'compiles without warnings'),
        ('WC', 'compiles with warnings'),
        ('NC', 'does not compile'),
    ]
    status = models.CharField(max_length=200, choices=STATUS_CHOICES)


section = models.ForeignKey('FileSection', on_delete=models.CASCADE)


class FileSectionStatusData(models.Model):
    data = models.CharField(max_length=200)
    section = models.ForeignKey('FileSection', on_delete=models.CASCADE)
