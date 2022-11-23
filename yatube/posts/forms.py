from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Сообщение', 'image': 'Картинка'}
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите ссообщение',
            'image': 'Выберите картинку'}
        # Добавили поле image в форму
        fields = ('group', 'text', 'image')
        widgets = {
            'text': forms.Textarea(attrs={"class": "form-control"}, ),
            'group': forms.Select(attrs={"class": "form-control"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария', }
        help_texts = {'text': 'Напишите ваш комментарий', }
