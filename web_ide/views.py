from django.forms import forms, CharField, Textarea, CharField, Textarea, ModelForm, Select, BooleanField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django import template
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from web_ide.models import *


# Create your views here.


class IndexView(generic.View):
    template_name = 'web_ide/index.html'

    @classmethod
    def get_context(cls, request):
        return {
            # parent directory is null, so this is a root directory
            'file_system_dir_roots': Directory.objects.filter(
                parent_directory=None,
                availability=True,
                owner=request.user),
            'file_system_file_roots': File.objects.filter(
                parent_directory=None,
                availability=True,
                owner=request.user),
            'files': File.objects.all(),
            'directories': Directory.objects.all(),
            'standard_form': StandardForm(),
            'optimization_form': OptimizationForm(),
            'processor_form': ProcessorForm(),
            'compile_form': CompileForm(),
        }

    def get(self, request):
        context = self.get_context(request)
        return render(request, self.template_name, context)


class FileView(generic.View):
    template_name = 'web_ide/index.html'

    def get_context(self, request, pk):
        context = IndexView.get_context(request=request)
        context['file'] = File.objects.get(pk=pk)
        context['compilable'] = True
        return context

    def get(self, request, pk):
        return render(request, self.template_name, self.get_context(request=request, pk=pk))

    def post(self, request, pk):
        context = self.get_context(request=request, pk=pk)
        form = StandardForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, context)
        context['compiled'] = True
        standard = request.POST.get('standard')
        processor = request.POST.get('processor')
        optimization = request.POST.get('optimization')

        return_code = context['file'].compile(standard=standard, optimization=optimization,
                                              processor=processor)
        return HttpResponseRedirect(reverse('web_ide:file', args=(pk,)))


class AddDirectoryForm(forms.Form):
    name = CharField(label='Name', max_length=100)
    description = CharField(label='Description', max_length=100, required=False)


class AddDirectoryView(generic.View):
    template_name = 'web_ide/add_directory.html'

    def get_context(self, request, pk):
        context = IndexView.get_context(request=request)
        context['add_directory_form'] = AddDirectoryForm()
        context['parent_directory'] = Directory.objects.get(pk=pk) if pk else None
        return context

    def get(self, request, pk=None):
        context = self.get_context(request=request, pk=pk)
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        context = self.get_context(request=request, pk=pk)
        form = AddDirectoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            parent_directory = Directory.objects.get(pk=pk) if pk else None
            if parent_directory:
                parent_directory.add_directory(name=name, description=description, owner=request.user)
            else:
                Directory.add_directory_in_root(name=name, description=description, owner=request.user)
            return HttpResponseRedirect(reverse('web_ide:index'))
        else:
            return render(request, self.template_name, context)


class AddFileForm(forms.Form):
    name = CharField(label='Name', max_length=100)
    description = CharField(label='Description', max_length=100, required=False)
    # allow new lines in content
    content = CharField(label='Content', widget=Textarea)


class AddFileView(generic.View):
    template_name = 'web_ide/add_file.html'

    def get_context(self, request, pk):
        context = IndexView.get_context(request=request)
        context['add_file_form'] = AddFileForm()
        context['parent_directory'] = Directory.objects.get(pk=pk) if pk else None
        return context

    def get(self, request, pk=None):
        context = self.get_context(request=request, pk=pk)
        return render(request, self.template_name, context)

    def post(self, request, pk=None):

        context = self.get_context(request=request, pk=pk)
        form = AddFileForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            content = form.cleaned_data['content']
            parent_directory = Directory.objects.get(pk=pk) if pk else None
            new_file = None
            if parent_directory:
                new_file = parent_directory.add_file(name=name, description=description, content=content,
                                                     owner=request.user)
            else:
                new_file = File.add_file_in_root(name=name, description=description, content=content,
                                                 owner=request.user)
            # redirect to /web_ide/<file_id>/
            if new_file:
                return HttpResponseRedirect(reverse('web_ide:file', args=(new_file.id,)))
            else:
                return HttpResponseRedirect(reverse('web_ide:index'))


        else:
            context['add_file_form'] = form
            return render(request, self.template_name, context)


class DeleteView(generic.View):

    def get(self, request, pk):
        file_system_object = FileSystemObject.objects.get(pk=pk)
        file_system_object.delete()
        return HttpResponseRedirect(reverse('web_ide:index'))


class AddOrRemoveTreeView(generic.View):
    template_name = 'web_ide/add_or_remove.html'

    def get(self, request):
        return render(request, self.template_name, IndexView.get_context(request=request))


STANDARD_CHOICES = (
    ('--std-c89', 'C89'),
    ('--std-c99', 'C99'),
    ('--std-c11', 'C11'),
)


class StandardForm(forms.Form):
    standard = CharField(label='Standard', widget=Select(choices=STANDARD_CHOICES))


OPTIMIZATION_CHOICES = (
    ('--opt-code-size', 'Optimize for code size'),
    ('--opt-code-speed', 'Optimize for code speed'),
    ('--no-peep', 'Disable peephole optimizations'),
)


class OptimizationForm(forms.Form):
    optimization = CharField(label='Optimization', widget=Select(choices=OPTIMIZATION_CHOICES))


PROCESSOR_CHOICES = (
    ('-mmcs51', 'MCS51'),
    ('-mz80', 'Z80'),
    ('-mstm8', 'STM8'),
)


class ProcessorForm(forms.Form):
    processor = CharField(label='Processor', widget=Select(choices=PROCESSOR_CHOICES))


class CompileForm(forms.Form):
    standard = CharField(label='Standard', widget=Select(choices=STANDARD_CHOICES))
    optimization = CharField(label='Optimization', widget=Select(choices=OPTIMIZATION_CHOICES))
    processor = CharField(label='Processor', widget=Select(choices=PROCESSOR_CHOICES))
