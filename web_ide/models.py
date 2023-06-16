import subprocess
from abc import abstractmethod

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
import os


# Create your models here.

class FileSystemObject(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)
    creation_date = models.DateTimeField('date created', default=timezone.now)
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

    @abstractmethod
    def is_directory(self):
        pass


class Directory(FileSystemObject):

    @classmethod
    def add_directory_in_root(cls, name, description=""):
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                description=description,
                parent_directory=None).exists():
            new_directory = Directory(name=name, description=description)
            new_directory.save()
            return new_directory

    def add_directory(self, name, description="", ):
        # ensure that the directory does not already exist
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                parent_directory=self).exists():
            new_directory = Directory(name=name, description=description, parent_directory=self)
            new_directory.save()
            return new_directory

    def add_file(self, name, content="", description=""):
        # ensure that the file does not already exist
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                parent_directory=self).exists():
            new_file = File(
                name=name,
                description=description,
                content=content,
                parent_directory=self)
            new_file.save()
            new_file.section_content()
            return new_file

    def is_directory(self):
        return True

    def delete(self, using=None, keep_parents=False):
        print("deleting directory " + self.name)
        self.availability = False
        self.availability_change_date = timezone.now()
        self.save()
        for child in File.objects.filter(parent_directory=self):
            child.delete()
        for child in Directory.objects.filter(parent_directory=self):
            child.delete()

    def generate_subtree(self):
        ret = {
            'type': 'directory',
            'pk': self.pk,
            'name': self.name,
            'description': self.description,
            'children_directories': [],
            'children_files': []
        }
        for child in self.children_directories().filter(availability=True):
            ret['children_directories'].append(child.generate_subtree())
        for child in self.children_files().filter(availability=True):
            ret['children_files'].append(child.generate_subtree())
        return ret


class File(FileSystemObject):
    content = models.TextField(blank=True, default='// this is content of file ' + str(super))
    compiled_content = models.TextField(blank=True, default="")

    @classmethod
    def add_file_in_root(cls, name, content="", description=""):
        if not FileSystemObject.objects.filter(
                availability=True,
                name=name,
                parent_directory=None).exists():
            new_file = File(name=name, content=content, description=description)
            new_file.save()
            new_file.section_content()
            return new_file

    @staticmethod
    def post_save(sender, instance, created, **kwargs):
        instance.section_content()

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
            FileSection.objects.create(file=self, begin=begin, end=end - 1).save()
        return

    def is_directory(self):
        return False

    def delete(self, using=None, keep_parents=False):
        self.availability = False
        self.availability_change_date = timezone.now()
        self.save()

    def compile(self, args):
        print(args)
        sc_filename = self.name + ".c"
        asm_filename = self.name + ".asm"
        ret = {
            'compilation_success': False,
            'stdout': '',
            'stderr': ''
        }
        with open(sc_filename, "w") as source_code:
            source_code.write(self.content)
            source_code.close()
            # compile file using sdcc
            sp = subprocess.Popen(["sdcc", "-S", sc_filename, "-o", asm_filename,
                                   ] + args,)
            sp.wait()
            if sp.returncode == 0:
                with open(asm_filename, "r") as compiled_code:
                    self.compiled_content = compiled_code.read()
                    compiled_code.close()
                os.remove(asm_filename)
            else:
                self.compiled_content = ""
            os.remove(sc_filename)
            ret['compilation_success'] = sp.returncode == 0
            ret['stdout'] = sp.stdout
            ret['stderr'] = sp.stderr
        self.save()
        return ret

    def generate_subtree(self):
        return {
            'type': 'file',
            'pk': self.pk,
            'name': self.name,
            'description': self.description
        }

    def get_compiled_content_by_sections(self):
        ret = []
        acc = ''
        cnt_lines = 0
        for line in self.compiled_content.splitlines(True):
            if line == ';--------------------------------------------------------\n':
                if cnt_lines == 2:
                    ret.append(acc)
                    acc = ''
                    cnt_lines = 0
                cnt_lines += 1
            acc += line
        ret.append(acc)
        return ret

    def get_content_by_sections(self):
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
            if li == sections[index].begin and acc != '':
                ret.append(acc)
                acc = ''
            acc += line
            if li == sections[index].end and acc != '':
                index += 1
                ret.append(acc)
                acc = ''
        if acc != '':
            ret.append(acc)
        return ret

    def __str__(self):
        return self.name


post_save.connect(File.post_save, sender=File)


def generate_file_tree():
    ret = {
        'root': {
            'children_directories': [],
            'children_files': []
        }
    }
    for child in Directory.objects.filter(parent_directory=None, availability=True):
        ret['root']['children_directories'].append(child.generate_subtree())
    for child in File.objects.filter(parent_directory=None, availability=True):
        ret['root']['children_files'].append(child.generate_subtree())
    return ret


class FileSection(models.Model):
    name = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    creation_date = models.DateTimeField('date created', default=timezone.now)
    begin = models.IntegerField()
    end = models.IntegerField()

    file = models.ForeignKey('File', on_delete=models.CASCADE)

    def __str__(self):
        return "file: " + str(self.file) + " section: " + str(self.begin) + "-" + str(self.end)
