# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Language'
        db.create_table('base_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['Language'])

        # Adding model 'Country'
        db.create_table('base_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['Country'])

        # Adding model 'LanguageCountry'
        db.create_table('base_languagecountry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Country'])),
        ))
        db.send_create_signal('base', ['LanguageCountry'])
        
        # Adding model 'NameCity'
        db.create_table('base_namecity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('base', ['NameCity'])

        # Adding model 'City'
        db.create_table('base_city', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone_code', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('base', ['City'])

        # Adding M2M table for field name on 'City'
        db.create_table('base_city_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('city', models.ForeignKey(orm['base.city'], null=False)),
            ('namecity', models.ForeignKey(orm['base.namecity'], null=False))
        ))
        db.create_unique('base_city_name', ['city_id', 'namecity_id'])

        # Adding model 'StreetType'
        db.create_table('base_streettype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['StreetType'])

        # Adding model 'Metro'
        db.create_table('base_metro', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['Metro'])

        # Adding model 'CinemaCircuit'
        db.create_table('base_cinemacircuit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['CinemaCircuit'])

        # Adding model 'Version'
        db.create_table('base_version', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['Version'])

        # Adding model 'Genre'
        db.create_table('base_genre', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['Genre'])

        # Adding model 'Runtime'
        db.create_table('base_runtime', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('runtime', self.gf('django.db.models.fields.IntegerField')()),
            ('runtime_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Runtime'])

        # Adding model 'Budget'
        db.create_table('base_budget', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('budget', self.gf('django.db.models.fields.BigIntegerField')()),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('base', ['Budget'])

        # Adding model 'ImageParameter'
        db.create_table('base_imageparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dimension', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('aspect_ratio', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('base', ['ImageParameter'])

        # Adding model 'SoundParameter'
        db.create_table('base_soundparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sound', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('soundsystem', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('base', ['SoundParameter'])

        # Adding model 'Action'
        db.create_table('base_action', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['Action'])

        # Adding model 'StatusAct'
        db.create_table('base_statusact', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['StatusAct'])

        # Adding model 'CarrierType'
        db.create_table('base_carriertype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['CarrierType'])

        # Adding model 'CarrierLayer'
        db.create_table('base_carrierlayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['CarrierLayer'])

        # Adding model 'CarrierRipType'
        db.create_table('base_carrierriptype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['CarrierRipType'])

        # Adding model 'CarrierTapeCategorie'
        db.create_table('base_carriertapecategorie', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['CarrierTapeCategorie'])

        # Adding model 'CopyFilmType'
        db.create_table('base_copyfilmtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['CopyFilmType'])

        # Adding model 'CopyFilmFormat'
        db.create_table('base_copyfilmformat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['CopyFilmFormat'])

        # Adding model 'CopyFilmAddValue'
        db.create_table('base_copyfilmaddvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['CopyFilmAddValue'])

        # Adding model 'NamePerson'
        db.create_table('base_nameperson', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('base', ['NamePerson'])

        # Adding model 'Person'
        db.create_table('base_person', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('iid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('kid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('male', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('born', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Country'], null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Person'])

        # Adding M2M table for field name on 'Person'
        db.create_table('base_person_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('person', models.ForeignKey(orm['base.person'], null=False)),
            ('nameperson', models.ForeignKey(orm['base.nameperson'], null=False))
        ))
        db.create_unique('base_person_name', ['person_id', 'nameperson_id'])


        # Adding model 'Interface'
        db.create_table('base_interface', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('browser', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('display', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('timezone', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.City'], null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Interface'])
        
        # Adding model 'Accounts'
        db.create_table('base_accounts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('login', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('validation_code', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('auth_status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('fullname', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('born', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('male', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('avatar', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Accounts'])
        
        # Adding model 'Profile'
        db.create_table('base_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Person'], null=True)),
            ('personinterface', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.PersonInterface'], null=True)),
            ('login_counter', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('auth_status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('folder', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('base', ['Profile'])

        # Adding M2M table for field interface on 'Profile'
        db.create_table('base_profile_interface', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['base.Profile'], null=False)),
            ('interface', models.ForeignKey(orm['base.Interface'], null=False))
        ))
        db.create_unique('base_profile_interface', ['profile_id', 'interface_id'])

        # Adding M2M table for field accounts on 'Profile'
        db.create_table('base_profile_accounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['base.Profile'], null=False)),
            ('accounts', models.ForeignKey(orm['base.Accounts'], null=False))
        ))
        db.create_unique('base_profile_accounts', ['profile_id', 'accounts_id'])
        
        
        # Adding model 'PersonInterface'
        db.create_table('base_personinterface', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('option1', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('option2', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('option3', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('option4', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('first_change', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('changed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('base', ['PersonInterface'])
        
        # Adding model 'APILogger'
        db.create_table('base_apilogger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('details', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('event', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('base', ['APILogger'])
        
        # Adding model 'NameProduct'
        db.create_table('base_nameproduct', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'], blank=True, null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('base', ['NameProduct'])
        
        
        # Adding model 'Films'
        db.create_table('base_films', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('release_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('release_end', self.gf('django.db.models.fields.DateField')(db_index=True, null=True, blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('film_type', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('runtime', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='runtime_films', null=True, to=orm['base.Runtime'])),
            ('rated', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('budget', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='budget_films', null=True, to=orm['base.Budget'])),
            ('image_parameter', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='image_films', null=True, to=orm['base.ImageParameter'])),
            ('sound_parameter', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sound_films', null=True, to=orm['base.SoundParameter'])),
        ))
        db.send_create_signal('base', ['Films'])

        # Adding M2M table for field name on 'Films'
        db.create_table('base_films_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('films', models.ForeignKey(orm['base.films'], null=False)),
            ('nameproduct', models.ForeignKey(orm['base.nameproduct'], null=False))
        ))
        db.create_unique('base_films_name', ['films_id', 'nameproduct_id'])

        # Adding M2M table for field countrys on 'Films'
        db.create_table('base_films_countrys', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('films', models.ForeignKey(orm['base.films'], null=False)),
            ('country', models.ForeignKey(orm['base.country'], null=False))
        ))
        db.create_unique('base_films_countrys', ['films_id', 'country_id'])

        # Adding M2M table for field genre on 'Films'
        db.create_table('base_films_genre', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('films', models.ForeignKey(orm['base.films'], null=False)),
            ('genre', models.ForeignKey(orm['base.genre'], null=False))
        ))
        db.create_unique('base_films_genre', ['films_id', 'genre_id'])

        # Adding model 'Logger'
        db.create_table('base_logger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=256, null=True, blank=True)),
            ('obj_name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('extra', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('event', self.gf('django.db.models.fields.IntegerField')()),
            ('code', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('base', ['Logger'])
        
        # Adding model 'IMDB'
        db.create_table('base_imdb', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_imdb', self.gf('django.db.models.fields.BigIntegerField')()),
            ('rating', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('base', ['IMDB'])

        # Adding model 'RelationFP'
        db.create_table('base_relationfp', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Person'])),
            ('status_act', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.StatusAct'])),
            ('action', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Action'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Films'])),
        ))
        db.send_create_signal('base', ['RelationFP'])

        # Adding model 'AlterStreetType'
        db.create_table('base_alterstreettype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.StreetType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal('base', ['AlterStreetType'])

        # Adding model 'ImportSources'
        db.create_table('base_importsources', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=256)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('base', ['ImportSources'])

        # Adding model 'FilmsSources'
        db.create_table('base_filmssources', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_films', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Films'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.ImportSources'])),
            ('id_films_sources', self.gf('django.db.models.fields.BigIntegerField')()),
        ))
        db.send_create_signal('base', ['FilmsSources'])

        # Adding model 'Phone'
        db.create_table('base_phone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('phone_type', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
        ))
        db.send_create_signal('base', ['Phone'])

        # Adding model 'Site'
        db.create_table('base_site', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('site_type', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
        ))
        db.send_create_signal('base', ['Site'])
        
        # Adding model 'NameCinema'
        db.create_table('base_namecinema', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('base', ['NameCinema'])

        # Adding model 'Cinema'
        db.create_table('base_cinema', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.City'])),
            ('cinema_circuit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.CinemaCircuit'], null=True)),
            ('street_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.StreetType'], null=True)),
            ('street_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('number_housing', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('number_hous', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('letter_housing', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('opening', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('base', ['Cinema'])

        # Adding M2M table for field metro on 'Cinema'
        db.create_table('base_cinema_metro', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cinema', models.ForeignKey(orm['base.cinema'], null=False)),
            ('metro', models.ForeignKey(orm['base.metro'], null=False))
        ))
        db.create_unique('base_cinema_metro', ['cinema_id', 'metro_id'])

        # Adding M2M table for field phone on 'Cinema'
        db.create_table('base_cinema_phone', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cinema', models.ForeignKey(orm['base.cinema'], null=False)),
            ('phone', models.ForeignKey(orm['base.phone'], null=False))
        ))
        db.create_unique('base_cinema_phone', ['cinema_id', 'phone_id'])

        # Adding M2M table for field site on 'Cinema'
        db.create_table('base_cinema_site', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cinema', models.ForeignKey(orm['base.cinema'], null=False)),
            ('site', models.ForeignKey(orm['base.site'], null=False))
        ))
        db.create_unique('base_cinema_site', ['cinema_id', 'site_id'])
        
        # Adding M2M table for field name on 'Cinema'
        db.create_table('base_cinema_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cinema', models.ForeignKey(orm['base.cinema'], null=False)),
            ('namecinema', models.ForeignKey(orm['base.namecinema'], null=False))
        ))
        db.create_unique('base_cinema_name', ['cinema_id', 'namecinema_id'])

        # Adding model 'NameHall'
        db.create_table('base_namehall', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Language'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('base', ['NameHall'])

        # Adding model 'Hall'
        db.create_table('base_hall', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('seats', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('screen_size_w', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('screen_size_h', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image_format', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('sound_format', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('cinema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Cinema'])),
            ('max_price', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('min_price', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Hall'])

        # Adding M2M table for field name on 'Hall'
        db.create_table('base_hall_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hall', models.ForeignKey(orm['base.hall'], null=False)),
            ('namehall', models.ForeignKey(orm['base.namehall'], null=False))
        ))
        db.create_unique('base_hall_name', ['hall_id', 'namehall_id'])


        # Adding model 'Demonstration'
        db.create_table('base_demonstration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Hall'])),
        ))
        db.send_create_signal('base', ['Demonstration'])

        # Adding model 'Session'
        db.create_table('base_session', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('demonstration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Demonstration'])),
            ('number', self.gf('django.db.models.fields.related.PositiveIntegerField')()),
            ('average_price', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('number_people', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Session'])

        # Adding M2M table for field film on 'Session'
        db.create_table('base_session_film', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('session', models.ForeignKey(orm['base.session'], null=False)),
            ('nameproduct', models.ForeignKey(orm['base.nameproduct'], null=False))
        ))
        db.create_unique('base_session_film', ['session_id', 'nameproduct_id'])


        # Adding model 'HallsSources'
        db.create_table('base_hallssources', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_hall', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Hall'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.ImportSources'])),
            ('url_hall_sources', self.gf('django.db.models.fields.URLField')(max_length=256)),
        ))
        db.send_create_signal('base', ['HallsSources'])




    def backwards(self, orm):
    
        # Deleting model 'Language'
        db.delete_table('base_language')

        # Deleting model 'Country'
        db.delete_table('base_country')

        # Deleting model 'Country'
        db.delete_table('base_languagecountry')
        
        # Deleting model 'NameCity'
        db.delete_table('base_namecity')

        # Deleting model 'City'
        db.delete_table('base_city')

        # Removing M2M table for field name on 'City'
        db.delete_table('base_city_name')

        # Deleting model 'StreetType'
        db.delete_table('base_streettype')

        # Deleting model 'Metro'
        db.delete_table('base_metro')

        # Deleting model 'CinemaCircuit'
        db.delete_table('base_cinemacircuit')

        # Deleting model 'Version'
        db.delete_table('base_version')

        # Deleting model 'Genre'
        db.delete_table('base_genre')

        # Deleting model 'Runtime'
        db.delete_table('base_runtime')

        # Deleting model 'Budget'
        db.delete_table('base_budget')

        # Deleting model 'ImageParameter'
        db.delete_table('base_imageparameter')

        # Deleting model 'SoundParameter'
        db.delete_table('base_soundparameter')

        # Deleting model 'CarrierType'
        db.delete_table('base_carriertype')

        # Deleting model 'CarrierLayer'
        db.delete_table('base_carrierlayer')

        # Deleting model 'CarrierRipType'
        db.delete_table('base_carrierriptype')

        # Deleting model 'CarrierTapeCategorie'
        db.delete_table('base_carriertapecategorie')

        # Deleting model 'Action'
        db.delete_table('base_action')

        # Deleting model 'StatusAct'
        db.delete_table('base_statusact')

        # Deleting model 'CopyFilmType'
        db.delete_table('base_copyfilmtype')

        # Deleting model 'CopyFilmFormat'
        db.delete_table('base_copyfilmformat')

        # Deleting model 'CopyFilmAddValue'
        db.delete_table('base_copyfilmaddvalue')

        # Deleting model 'NamePerson'
        db.delete_table('base_nameperson')

        # Deleting model 'Person'
        db.delete_table('base_person')

        # Removing M2M table for field name on 'Person'
        db.delete_table('base_person_name')

        # Deleting model 'Interface'
        db.delete_table('base_interface')
        
        # Deleting model 'Accounts'
        db.delete_table('base_accounts')
        
        # Deleting model 'Profile'
        db.delete_table('base_profile')
        
        # Deleting model 'PersonInterface'
        db.delete_table('base_personinterface')

        # Deleting model 'APILogger'
        db.delete_table('base_apilogger')
        
        # Deleting model 'NameProduct'
        db.delete_table('base_nameproduct')

        # Deleting model 'Films'
        db.delete_table('base_films')

        # Removing M2M table for field name on 'Films'
        db.delete_table('base_films_name')

        # Removing M2M table for field name on 'Films'
        db.delete_table('base_films_countrys')

        # Removing M2M table for field name on 'Films'
        db.delete_table('base_films_genre')
        
        # Deleting model 'Logger'
        db.delete_table('base_logger')

        # Deleting model 'IMDB'
        db.delete_table('base_imdb')

        # Deleting model 'RelationFP'
        db.delete_table('base_relationfp')

        # Deleting model 'AlterStreetType'
        db.delete_table('base_alterstreettype')

        # Deleting model 'ImportSources'
        db.delete_table('base_importsources')

        # Deleting model 'FilmSources'
        db.delete_table('base_filmsources')
      
        # Deleting model 'Phone'
        db.delete_table('base_phone')

        # Deleting model 'Site'
        db.delete_table('base_site')
        
        # Deleting model 'NameCinema'
        db.delete_table('base_namecinema')

        # Deleting model 'Cinema'
        db.delete_table('base_cinema')

        # Removing M2M table for field name on 'Cinema'
        db.delete_table('base_cinema_name')

        # Deleting model 'NameHall'
        db.delete_table('base_namehall')

        # Deleting model 'Hall'
        db.delete_table('base_hall')

        # Removing M2M table for field name on 'Hall'
        db.delete_table('base_hall_name')
        
        # Deleting model 'Demonstration'
        db.delete_table('base_demonstration')

        # Deleting model 'Session'
        db.delete_table('base_session')

        # Removing M2M table for field film on 'Session'
        db.delete_table('base_session_film')

        # Deleting model 'HallSources'
        db.delete_table('base_hallsources')


        
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'base.accounts': {
            'Meta': {'object_name': 'Accounts'},
            'auth_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'avatar': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'born': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'male': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'validation_code': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'base.action': {
            'Meta': {'object_name': 'Action'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'base.alterstreettype': {
            'Meta': {'object_name': 'AlterStreetType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.StreetType']"})
        },
        'base.apilogger': {
            'Meta': {'object_name': 'APILogger'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'details': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'event': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'base.budget': {
            'Meta': {'object_name': 'Budget'},
            'budget': ('django.db.models.fields.BigIntegerField', [], {}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'base.carrierlayer': {
            'Meta': {'object_name': 'CarrierLayer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.carrierriptype': {
            'Meta': {'object_name': 'CarrierRipType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.carriertapecategorie': {
            'Meta': {'object_name': 'CarrierTapeCategorie'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.carriertype': {
            'Meta': {'object_name': 'CarrierType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.cinema': {
            'Meta': {'object_name': 'Cinema'},
            'cinema_circuit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.CinemaCircuit']", 'null': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.City']"}),
            'code': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter_housing': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'metro': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Metro']", 'null': 'True', 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['base.NameCinema']", 'null': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'number_hous': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'number_housing': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'opening': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Phone']", 'null': 'True', 'symmetrical': 'False'}),
            'site': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Site']", 'null': 'True', 'symmetrical': 'False'}),
            'street_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'street_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.StreetType']", 'null': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'})
        },
        'base.cinemacircuit': {
            'Meta': {'object_name': 'CinemaCircuit'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['base.NameCity']", 'null': 'True', 'blank': 'True'}),
            'phone_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'base.copyfilmaddvalue': {
            'Meta': {'object_name': 'CopyFilmAddValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'base.copyfilmformat': {
            'Meta': {'object_name': 'CopyFilmFormat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'base.copyfilmtype': {
            'Meta': {'object_name': 'CopyFilmType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'base.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.demonstration': {
            'Meta': {'object_name': 'Demonstration'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Hall']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'base.films': {
            'Meta': {'object_name': 'Films'},
            'budget': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'budget_films'", 'null': 'True', 'to': "orm['base.Budget']"}),
            'countrys': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'countrys_films'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['base.Country']"}),
            'film_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'genre': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'genre_films'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['base.Genre']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_parameter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'image_films'", 'null': 'True', 'to': "orm['base.ImageParameter']"}),
            'key_creators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'key_creators_films'", 'to': "orm['base.Person']", 'through': "orm['base.RelationFP']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'name': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'name_films'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['base.NameProduct']"}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rated': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'release_end': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'release_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'runtime': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'runtime_films'", 'null': 'True', 'to': "orm['base.Runtime']"}),
            'sound_parameter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sound_films'", 'null': 'True', 'to': "orm['base.SoundParameter']"})
        },
        'base.filmssources': {
            'Meta': {'object_name': 'FilmsSources'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_films': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Films']"}),
            'id_films_sources': ('django.db.models.fields.BigIntegerField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.ImportSources']"})
        },
        'base.genre': {
            'Meta': {'object_name': 'Genre'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.hall': {
            'Meta': {'object_name': 'Hall'},
            'cinema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Cinema']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_format': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'max_price': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['base.NameHall']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'screen_size_h': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'screen_size_w': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'seats': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sound_format': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        },
        'base.hallssources': {
            'Meta': {'object_name': 'HallsSources'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_hall': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Hall']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.ImportSources']"}),
            'url_hall_sources': ('django.db.models.fields.URLField', [], {'max_length': '256'})
        },
        'base.imageparameter': {
            'Meta': {'object_name': 'ImageParameter'},
            'aspect_ratio': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'dimension': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'base.imdb': {
            'Meta': {'object_name': 'IMDB'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_imdb': ('django.db.models.fields.BigIntegerField', [], {}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'base.importsources': {
            'Meta': {'object_name': 'ImportSources'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '256'})
        },
        'base.interface': {
            'Meta': {'object_name': 'Interface'},
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.City']", 'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'base.language': {
            'Meta': {'object_name': 'Language'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.languagecountry': {
            'Meta': {'object_name': 'LanguageCountry'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']"})
        },
        'base.logger': {
            'Meta': {'object_name': 'Logger'},
            'code': ('django.db.models.fields.IntegerField', [], {}),
            'event': ('django.db.models.fields.IntegerField', [], {}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'base.metro': {
            'Meta': {'object_name': 'Metro'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.namecinema': {
            'Meta': {'object_name': 'NameCinema'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'base.namecity': {
            'Meta': {'object_name': 'NameCity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'base.namehall': {
            'Meta': {'object_name': 'NameHall'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'base.nameperson': {
            'Meta': {'object_name': 'NamePerson'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'base.nameproduct': {
            'Meta': {'object_name': 'NameProduct'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Language']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'base.person': {
            'Meta': {'object_name': 'Person'},
            'born': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Country']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'kid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'male': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.NamePerson']", 'symmetrical': 'False'})
        },
        'base.personinterface': {
            'Meta': {'object_name': 'PersonInterface'},
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_change': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option1': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'option2': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'option3': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'option4': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'base.phone': {
            'Meta': {'object_name': 'Phone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'phone_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        },
        'base.profile': {
            'Meta': {'object_name': 'Profile'},
            'accounts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Accounts']", 'null': 'True', 'symmetrical': 'False'}),
            'auth_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'folder': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Interface']", 'null': 'True', 'symmetrical': 'False'}),
            'login_counter': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Person']", 'null': 'True'}),
            'personinterface': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.PersonInterface']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'base.relationfp': {
            'Meta': {'object_name': 'RelationFP'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Action']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Person']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Films']"}),
            'status_act': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.StatusAct']"})
        },
        'base.runtime': {
            'Meta': {'object_name': 'Runtime'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'runtime': ('django.db.models.fields.IntegerField', [], {}),
            'runtime_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'base.session': {
            'Meta': {'object_name': 'Session'},
            'average_price': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'demonstration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Demonstration']"}),
            'film': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.NameProduct']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'number_people': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'base.site': {
            'Meta': {'object_name': 'Site'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'base.soundparameter': {
            'Meta': {'object_name': 'SoundParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sound': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'soundsystem': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'base.statusact': {
            'Meta': {'object_name': 'StatusAct'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'base.streettype': {
            'Meta': {'object_name': 'StreetType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'base.version': {
            'Meta': {'object_name': 'Version'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['base']
