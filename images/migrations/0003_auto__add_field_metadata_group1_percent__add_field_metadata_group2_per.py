# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Metadata.group1_percent'
        db.add_column('images_metadata', 'group1_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group2_percent'
        db.add_column('images_metadata', 'group2_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group3_percent'
        db.add_column('images_metadata', 'group3_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group4_percent'
        db.add_column('images_metadata', 'group4_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group5_percent'
        db.add_column('images_metadata', 'group5_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group6_percent'
        db.add_column('images_metadata', 'group6_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group7_percent'
        db.add_column('images_metadata', 'group7_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Metadata.group1_percent'
        db.delete_column('images_metadata', 'group1_percent')

        # Deleting field 'Metadata.group2_percent'
        db.delete_column('images_metadata', 'group2_percent')

        # Deleting field 'Metadata.group3_percent'
        db.delete_column('images_metadata', 'group3_percent')

        # Deleting field 'Metadata.group4_percent'
        db.delete_column('images_metadata', 'group4_percent')

        # Deleting field 'Metadata.group5_percent'
        db.delete_column('images_metadata', 'group5_percent')

        # Deleting field 'Metadata.group6_percent'
        db.delete_column('images_metadata', 'group6_percent')

        # Deleting field 'Metadata.group7_percent'
        db.delete_column('images_metadata', 'group7_percent')


    models = {
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'camera': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Metadata']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'group1_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group2_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group3_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group4_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group5_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group6_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group7_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.IntegerField', [], {}),
            'water_quality': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
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
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['images']
