from django.forms import forms, CharField, Textarea, CharField, Textarea, ModelForm, Select, BooleanField
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, routers
from django.shortcuts import render
from django import template
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from web_ide.models import *
from web_ide.serializers import *
import json

# Create your views here.

router = routers.DefaultRouter()


class FileTreeView(APIView):

    def get(self, request, *args, **kwargs):
        return Response(generate_file_tree())


class FileView(APIView):

    def get(self, request, pk, *args, **kwargs):
        file = File.objects.get(pk=pk)
        serializer = FileSerializer(file)
        return Response(serializer.data)


class CompileView(APIView):

    def post(self, request, *args, **kwargs):
        print(request.data.get('pk'))
        file = File.objects.get(pk=request.data['pk'])
        output = file.compile(request.data.get('args'))
        return Response({'status': 'success'})


class DeleteView(APIView):

    def post(self, request, *args, **kwargs):
        fso = None
        if File.objects.filter(pk=request.data['pk']).exists():
            fso = File.objects.get(pk=request.data['pk'])
        elif Directory.objects.filter(pk=request.data['pk']).exists():
            fso = Directory.objects.get(pk=request.data['pk'])
        if fso is None:
            return HttpResponseBadRequest()
        fso.delete()
        return HttpResponse({'status': 'success'})


class AddView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        match data['type'], data['parent_pk']:
            case 'file', None:
                File.add_file_in_root(data['name'], data['content'], data['description'])
            case 'file', _:
                parent = Directory.objects.get(pk=data['parent_pk'])
                parent.add_file(data['name'], data['content'], data['description'])
            case 'directory', None:
                Directory.add_directory_in_root(data['name'], data['description'])
            case 'directory', _:
                parent = Directory.objects.get(pk=data['parent_pk'])
                parent.add_directory(data['name'], data['description'])
            case _:
                return HttpResponseBadRequest()
        return HttpResponse()
