# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for source in orm.Source.objects.all():
            if source.visibility == 'i':
                source.visibility = 'v'
                source.save()


    def backwards(self, orm):
        print """NOTE: We're rolling back a migration that turned invisible
        Sources into private Sources, but now, there's no way to know which
        private Sources were previously invisible.  So this migration
        rollback does nothing."""


    models = {
        'images.camerainfo': {
            'Meta': {'object_name': 'CameraInfo'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.IntegerField', [], {}),
            'water_quality': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'camera': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.CameraInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.point': {
            'Meta': {'object_name': 'Point'},
            'annotation_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'column': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Image']"}),
            'point_number': ('django.db.models.fields.IntegerField', [], {}),
            'row': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.source': {
            'Meta': {'object_name': 'Source'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key4': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key5': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'v'", 'max_length': '1'})
        }
    }

    complete_apps = ['images']
