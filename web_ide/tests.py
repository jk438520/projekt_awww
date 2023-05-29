from functools import reduce

from django.test import TestCase, RequestFactory
from web_ide.models import *
from web_ide.views import *

from django.contrib.auth.models import User


# Create your tests here.


class DirectoryTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_create_with_same_name(self):
        self.assertTrue(Directory.add_directory_in_root(name="test", owner=self.user))
        self.assertIsNone(Directory.add_directory_in_root(name="test", owner=self.user))

    def test_dir_in_dir(self):
        dir = Directory.add_directory_in_root(name="test", owner=self.user)
        self.assertTrue(dir.add_directory(name="test2", owner=self.user))
        self.assertEqual(dir.children_directories().count(), 1)
        self.assertEqual(dir.children_directories()[0].name, "test2")


example_content = """#include <stdio.h>
int function_one(){
   return 1;
}

int funtion_eleven(){
   int a = 10 + 1;
   return a;

}


int main() {
   printf("Hello, World!");
   return 0;
}"""


class FileTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_create_with_same_name(self):
        self.assertTrue(File.add_file_in_root(name="test", owner=self.user))
        self.assertIsNone(File.add_file_in_root(name="test", owner=self.user))

    def test_file_in_dir(self):
        dir = Directory.add_directory_in_root(name="test", owner=self.user)
        self.assertTrue(dir.add_file(name="test2", owner=self.user, content=example_content))
        self.assertEqual(dir.children_files().count(), 1)
        self.assertEqual(dir.children_files()[0].name, "test2")
        self.assertEqual(dir.children_files()[0].content, example_content)

    def test_files_in_different_dirs(self):
        dir1 = Directory.add_directory_in_root(name="dir1", owner=self.user)
        dir2 = Directory.add_directory_in_root(name="dir2", owner=self.user)
        self.assertTrue(dir1.add_file("file", self.user, example_content))
        self.assertTrue(dir2.add_file("file", self.user, example_content))


class DeleteTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_delete_file(self):
        file = File.add_file_in_root('file', self.user, example_content)
        self.assertTrue(file.availability)
        file.delete()
        self.assertFalse(file.availability)

    def test_delete_directory_with_file(self):
        dir = Directory.add_directory_in_root(name="dir1", owner=self.user)
        file = dir.add_file("file", self.user, example_content)
        self.assertTrue(dir.availability)
        self.assertTrue(file.availability)
        dir.delete()
        dir = Directory.objects.get(pk=dir.pk)
        file = File.objects.get(pk=file.pk)
        self.assertFalse(dir.availability)
        self.assertFalse(file.availability)


class SectionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_auto_section(self):
        file = File.add_file_in_root('file', self.user, example_content)
        file.section_content()
        sections = file.get_content_by_section()
        self.assertEqual(example_content, reduce(lambda x, y: x + y, sections, ""))
        for section in sections:
            self.assertTrue(section in example_content)


class IndexTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_index(self):
        self.client.login(username='test_user123', password='test_user123')
        response = self.client.get('/web_ide/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web_ide/index.html')


class DeleteViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')

    def test_delete_file(self):
        file = File.add_file_in_root('file', self.user, example_content)
        response = self.client.get('/web_ide/delete/' + str(file.pk) + '/')
        file = File.objects.get(pk=file.pk)
        self.assertFalse(file.availability)

    def test_delete_directory_with_file(self):
        dir = Directory.add_directory_in_root(name="dir1", owner=self.user)
        file = dir.add_file("file", self.user, example_content)
        self.client.get('/web_ide/delete/' + str(dir.pk) + '/')
        dir = Directory.objects.get(pk=dir.pk)
        file = File.objects.get(pk=file.pk)
        self.assertFalse(dir.availability)
        self.assertFalse(file.availability)


class AddFileViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')
        self.factory = RequestFactory()

    def test_add_file(self):
        request = self.factory.post('/web_ide/add_file/', {'name': 'test_file', 'content': example_content})
        request.user = self.user
        AddFileView.as_view()(request)
        self.assertEqual(len(File.objects.filter(name='test_file')), 1)

    def test_add_file_with_existing_name(self):
        File.add_file_in_root('test_file', self.user, example_content)
        self.test_add_file()


class AddDirectoryViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')
        self.factory = RequestFactory()

    def test_add_directory(self):
        request = self.factory.post('/web_ide/add_directory/', {'name': 'test_dir'})
        request.user = self.user
        AddDirectoryView.as_view()(request)
        self.assertEqual(len(Directory.objects.filter(name='test_dir')), 1)

    def test_add_directory_with_existing_name(self):
        Directory.add_directory_in_root('test_dir', self.user)
        self.test_add_directory()


class TestCompileView(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user123')
        self.factory = RequestFactory()

    def test_compile_no_args(self):
        file = File.add_file_in_root('file', self.user, example_content)
        self.assertEqual(file.compiled_content, "")
        request = self.factory.post('/web_ide/compile/' + str(file.pk) + '/', {})
        request.user = self.user
        CompileView.as_view()(request, pk=file.pk)
        file = File.objects.get(pk=file.pk)
        self.assertEqual(file.compiled_content, "")

    def test_compile_with_args(self):
        file = File.add_file_in_root('file', self.user, example_content)
        self.assertEqual(file.compiled_content, "")
        request = self.factory.post('/web_ide/compile/' + str(file.pk) + '/',
                                    {'standard': '--std-c11', 'optimization': '--opt-code-size', 'processor': '-mmcs51'})
        request.user = self.user
        CompileView.as_view()(request, pk=file.pk)
        file = File.objects.get(pk=file.pk)
        self.assertNotEquals(file.compiled_content, "")
