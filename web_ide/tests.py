from functools import reduce

from django.test import TestCase, RequestFactory
from web_ide.models import *
from web_ide.views import *


class DirectoryTest(TestCase):

    def test_create_with_same_name(self):
        self.assertTrue(Directory.add_directory_in_root(name="test"))
        self.assertIsNone(Directory.add_directory_in_root(name="test"))

    def test_dir_in_dir(self):
        dir = Directory.add_directory_in_root(name="test")
        self.assertTrue(dir.add_directory(name="test2"))
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


class FileTest(TestCase):

    def test_create_with_same_name(self):
        self.assertTrue(File.add_file_in_root(name="test"))
        self.assertIsNone(File.add_file_in_root(name="test"))

    def test_file_in_dir(self):
        dir = Directory.add_directory_in_root(name="test")
        self.assertTrue(dir.add_file(name="test2", content=example_content))
        self.assertEqual(dir.children_files().count(), 1)
        self.assertEqual(dir.children_files()[0].name, "test2")
        self.assertEqual(dir.children_files()[0].content, example_content)

    def test_files_in_different_dirs(self):
        dir1 = Directory.add_directory_in_root(name="dir1")
        dir2 = Directory.add_directory_in_root(name="dir2")
        self.assertTrue(dir1.add_file("file", example_content))
        self.assertTrue(dir2.add_file("file", example_content))


class DeleteTests(TestCase):

    def test_delete_file(self):
        file = File.add_file_in_root('file', example_content)
        self.assertTrue(file.availability)
        file.delete()
        self.assertFalse(file.availability)

    def test_delete_directory_with_file(self):
        dir = Directory.add_directory_in_root(name="dir1")
        file = dir.add_file("file", example_content)
        self.assertTrue(dir.availability)
        self.assertTrue(file.availability)
        dir.delete()
        dir = Directory.objects.get(pk=dir.pk)
        file = File.objects.get(pk=file.pk)
        self.assertFalse(dir.availability)
        self.assertFalse(file.availability)


class SectionTest(TestCase):

    def test_auto_section(self):
        file = File.add_file_in_root('file', example_content)
        sections = file.get_content_by_sections()
        self.assertEqual(example_content, reduce(lambda x, y: x + y, sections, ""))
        for section in sections:
            self.assertTrue(section in example_content)


class CompileTest(TestCase):

    def test_compile(self):
        file = File.add_file_in_root('file', example_content)
        file.compile([])
        self.assertTrue(file.compiled_content != "")
        self.assertTrue(file.compiled_content is not None)

    def test_different_compiles(self):
        file = File.add_file_in_root('file', example_content)
        args = ['--std-c89', '--opt-code-size', '--opt-code-speed', '--no-peep', '-mds390', '--24-bit', '--stack-10bit']
        file.compile(args)
        compile1 = file.compiled_content
        args = ['--std-c89', '--opt-code-size', '--opt-code-speed', '--no-peep', '-mmcs51', '--model-medium']
        file.compile(args)
        compile2 = file.compiled_content
        self.assertNotEqual(compile1, compile2)


class ApiTreeTest(TestCase):

    def setUp(self):

        dir1 = Directory.add_directory_in_root(name="dir1")
        dir2 = Directory.add_directory_in_root(name="dir2")
        dir1.add_file("file", example_content)
        dir2.add_file("file", example_content)

    def test_basic(self):
        response = self.client.get('/web_ide/file_tree/')
        self.assertEqual(response.status_code, 200)
        expected = {'root': {'children_directories': [
            {'type': 'directory', 'pk': 1, 'name': 'dir1', 'description': '', 'children_directories': [],
             'children_files': [{'type': 'file', 'pk': 3, 'name': 'file', 'description': ''}]},
            {'type': 'directory', 'pk': 2, 'name': 'dir2', 'description': '', 'children_directories': [],
             'children_files': [{'type': 'file', 'pk': 4, 'name': 'file', 'description': ''}]}], 'children_files': []}}

        self.assertEqual(response.json(), expected)

class ApiFileTest(TestCase):

    def setUp(self):
        self.file = File.add_file_in_root('file', example_content)

    def test_get(self):
        self.maxDiff = None
        response = self.client.get('/web_ide/file/1/')
        self.assertEqual(response.status_code, 200)
        print("this is response: ", response.json())
        expected = {'pk': 1, 'name': 'file', 'description': '', 'content': example_content, 'compiled_content': "", 'compiled_content_by_sections': ['']}
        response_data = response.json()
        response_data.pop('content_by_sections')
        self.assertEqual(response_data, expected)

class ApiCompileTest(TestCase):

    def setUp(self):
        self.file = File.add_file_in_root('file', example_content)

    def test_post(self):
        response = self.client.post("/web_ide/compile/", data={'pk': 1, 'args': ['--std-c89', '--opt-code-size', '--opt-code-speed', '--no-peep', '-mds390', '--24-bit', '--stack-10bit']})
        print(response.json())