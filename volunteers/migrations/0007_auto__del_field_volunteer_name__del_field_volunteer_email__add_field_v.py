# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Volunteer.name'
        db.delete_column(u'volunteers_volunteer', 'name')

        # Deleting field 'Volunteer.email'
        db.delete_column(u'volunteers_volunteer', 'email')

        # Adding field 'Volunteer.mugshot'
        db.add_column(u'volunteers_volunteer', 'mugshot',
                      self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100, blank=True),
                      keep_default=False)

        # Adding field 'Volunteer.privacy'
        db.add_column(u'volunteers_volunteer', 'privacy',
                      self.gf('django.db.models.fields.CharField')(default='registered', max_length=15),
                      keep_default=False)

        # Adding field 'Volunteer.language'
        db.add_column(u'volunteers_volunteer', 'language',
                      self.gf('django.db.models.fields.CharField')(default='en', max_length=5),
                      keep_default=False)

        # Adding field 'Volunteer.about_me'
        db.add_column(u'volunteers_volunteer', 'about_me',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


        # Changing field 'Volunteer.user'
        db.alter_column(u'volunteers_volunteer', 'user_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['auth.User']))
        # Adding unique constraint on 'Volunteer', fields ['user']
        db.create_unique(u'volunteers_volunteer', ['user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Volunteer', fields ['user']
        db.delete_unique(u'volunteers_volunteer', ['user_id'])

        # Adding field 'Volunteer.name'
        db.add_column(u'volunteers_volunteer', 'name',
                      self.gf('django.db.models.fields.CharField')(default='Nameless One', max_length=50),
                      keep_default=False)

        # Adding field 'Volunteer.email'
        db.add_column(u'volunteers_volunteer', 'email',
                      self.gf('django.db.models.fields.EmailField')(default='', max_length=75),
                      keep_default=False)

        # Deleting field 'Volunteer.mugshot'
        db.delete_column(u'volunteers_volunteer', 'mugshot')

        # Deleting field 'Volunteer.privacy'
        db.delete_column(u'volunteers_volunteer', 'privacy')

        # Deleting field 'Volunteer.language'
        db.delete_column(u'volunteers_volunteer', 'language')

        # Deleting field 'Volunteer.about_me'
        db.delete_column(u'volunteers_volunteer', 'about_me')


        # Changing field 'Volunteer.user'
        db.alter_column(u'volunteers_volunteer', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'volunteers.edition': {
            'Meta': {'ordering': "['-year']", 'object_name': 'Edition'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'volunteers.talk': {
            'Meta': {'ordering': "['date', 'start_time']", 'object_name': 'Talk'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'speaker': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'track': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Track']"})
        },
        u'volunteers.task': {
            'Meta': {'ordering': "['date', 'start_time']", 'object_name': 'Task'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'nbr_volunteers': ('django.db.models.fields.IntegerField', [], {}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'talk': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Talk']", 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.TaskTemplate']"}),
            'volunteers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['volunteers.Volunteer']", 'null': 'True', 'through': u"orm['volunteers.VolunteerTask']", 'blank': 'True'})
        },
        u'volunteers.taskcategory': {
            'Meta': {'ordering': "['name']", 'object_name': 'TaskCategory'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'volunteers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['volunteers.Volunteer']", 'null': 'True', 'through': u"orm['volunteers.VolunteerCategory']", 'blank': 'True'})
        },
        u'volunteers.tasktemplate': {
            'Meta': {'ordering': "['name']", 'object_name': 'TaskTemplate'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.TaskCategory']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'volunteers.track': {
            'Meta': {'ordering': "['date', 'start_time']", 'object_name': 'Track'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'volunteers.volunteer': {
            'Meta': {'object_name': 'Volunteer'},
            'about_me': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['volunteers.TaskCategory']", 'null': 'True', 'through': u"orm['volunteers.VolunteerCategory']", 'blank': 'True'}),
            'editions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['volunteers.Edition']", 'null': 'True', 'through': u"orm['volunteers.VolunteerStatus']", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5'}),
            'mugshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'registered'", 'max_length': '15'}),
            'signed_up': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'tasks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['volunteers.Task']", 'null': 'True', 'through': u"orm['volunteers.VolunteerTask']", 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'volunteer'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'volunteers.volunteercategory': {
            'Meta': {'object_name': 'VolunteerCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.TaskCategory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'volunteer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Volunteer']"})
        },
        u'volunteers.volunteerstatus': {
            'Meta': {'object_name': 'VolunteerStatus'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'edition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Edition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'volunteer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Volunteer']"})
        },
        u'volunteers.volunteertask': {
            'Meta': {'object_name': 'VolunteerTask'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Task']"}),
            'volunteer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['volunteers.Volunteer']"})
        }
    }

    complete_apps = ['volunteers']