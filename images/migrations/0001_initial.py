# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Source'
        db.create_table('images_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('visibility', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('key1', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('key2', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('key3', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('key4', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('key5', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('longitude', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('latitude', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
        ))
        db.send_create_signal('images', ['Source'])

        # Adding model 'CameraInfo'
        db.create_table('images_camerainfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('pixel_cm_ratio', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('photographer', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('water_quality', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
        ))
        db.send_create_signal('images', ['CameraInfo'])

        # Adding model 'Image'
        db.create_table('images_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('total_points', self.gf('django.db.models.fields.IntegerField')()),
            ('camera', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.CameraInfo'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Image'])

        # Adding model 'Point'
        db.create_table('images_point', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('row', self.gf('django.db.models.fields.IntegerField')()),
            ('column', self.gf('django.db.models.fields.IntegerField')()),
            ('point_number', self.gf('django.db.models.fields.IntegerField')()),
            ('annotation_status', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Image'])),
        ))
        db.send_create_signal('images', ['Point'])


    def backwards(self, orm):
        
        # Deleting model 'Source'
        db.delete_table('images_source')

        # Deleting model 'CameraInfo'
        db.delete_table('images_camerainfo')

        # Deleting model 'Image'
        db.delete_table('images_image')

        # Deleting model 'Point'
        db.delete_table('images_point')


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
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['images']
