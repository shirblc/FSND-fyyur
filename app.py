#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(240))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(240))
    shows = db.relationship('Show', backref='show_venue')

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(240))
    shows = db.relationship('Show', backref='show_artist')

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Get the current date and time
  current_datetime = datetime.now()

  # Get the data from the database
  data = []
  city_count = db.session.query(Venue.city, Venue.state, db.func.count(Venue.id)).group_by(Venue.city, Venue.state).all()
  venue_show_data = db.session.query(Venue.id, Venue.name, db.func.count(Show.id)).outerjoin(Show).group_by(Venue.id, Venue.name)

  # Add data to the data list
  for city in city_count:
      data.append({
        'city': city[0],
        'state': city[1],
        'venues': []
      })
      city_venue_data = venue_show_data.filter(Venue.city == city[0]).filter(Venue.state == city[1]).all()
      num_venues = city[2]
      # Add venues information
      for i in range(num_venues):
          data[len(data) - 1]['venues'].append({
            'id': city_venue_data[i][0],
            'name': city_venue_data[i][1],
            'num_upcoming_shows': city_venue_data[i][2]
          })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Gets the search term from the text field and searches in the database
  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike('%' + search_term + '%')).all()
  num_search_results = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike('%' + search_term + '%')).count()

  return render_template('pages/search_venues.html', results=search_results, search_term=search_term, num_search_results=num_search_results)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Get the current date and time
  current_datetime = datetime.now()

  # Get the venue details from the database
  venue_data = db.session.query(Venue).get(venue_id)
  venue_data.genres = str(venue_data.genres).split(',')
  past_shows = db.session.query(Show.venue_id, Show.start_time, Show.artist_id,
  Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < current_datetime).all()
  future_shows = db.session.query(Show.venue_id, Show.start_time, Show.artist_id,
  Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > current_datetime).all()
  past_shows_count = db.session.query(Show.venue_id, Show.start_time).filter(Show.venue_id == venue_id).filter(Show.start_time < current_datetime).count()
  future_shows_count = db.session.query(Show.venue_id, Show.start_time).filter(Show.venue_id == venue_id).filter(Show.start_time > current_datetime).count()

  return render_template('pages/show_venue.html', venue=venue_data, past_shows=past_shows,
  future_shows=future_shows, num_past_shows=past_shows_count, num_future_shows=future_shows_count)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  #Venue details as entered in the submitted form
  venue_name = request.form.get('name')
  venue_city = request.form.get('city')
  venue_state = request.form.get('state')
  venue_address = request.form.get('address')
  venue_phone = request.form.get('phone')
  venue_genres = ','.join(request.form.getlist('genres'))
  venue_fb_link = request.form.get('facebook_link')
  venue_website = request.form.get('website')
  venue_image = request.form.get('image_link')
  seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
  seeking_description = request.form.get('seeking_description')

  data = {}
  error = False

  #Try to add the data to the database
  try:
      #New venue object
      venue = Venue(name=venue_name, city=venue_city, state=venue_state,
      address=venue_address, phone=venue_phone, genres=venue_genres,
      facebook_link=venue_fb_link, website=venue_website, image_link=venue_image,
      seeking_talent=seeking_talent, seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()
      data['name'] = venue.name
  #If there's an error, rollback the session
  except:
      db.session.rollback()
      error = True
  #Close the connection either way
  finally:
      db.session.close()
  #If an error occurred, flash an error message
  if error:
      flash('An error occurred and the venue was not listed. Please try again.')
  #If there was no error, alert the user the venue was listed
  if not error:
      # on successful db insert, flash success
      flash('Venue ' + data['name'] + ' was successfully listed!')
  # TODO: modify data to be the data object returned from db insertion

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Gets the search term from the text field and searches the database
  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Artist.name, Artist.id).filter(Artist.name.ilike('%' + search_term + '%')).all()
  num_search_results = db.session.query(Artist.name, Artist.id).filter(Artist.name.ilike('%' + search_term + '%')).count()

  return render_template('pages/search_artists.html', results=search_results, search_term=search_term, num_search_results=num_search_results)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # Gets the current date
  current_datetime = datetime.now()

  # Gets the artist data to display on the page
  artist_data = db.session.query(Artist).get(artist_id)
  artist_data.genres = str(artist_data.genres).split(',')
  past_shows = db.session.query(Show.venue_id, Show.start_time, Venue.name.label('venue_name'),
  Venue.image_link.label('venue_image_link')).select_from(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < current_datetime).all()
  future_shows = db.session.query(Show.venue_id, Show.start_time, Venue.name.label('venue_name'),
  Venue.image_link.label('venue_image_link')).select_from(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > current_datetime).all()
  num_past_shows = db.session.query(Show.artist_id, Show.start_time).filter(Show.artist_id == artist_id).filter(Show.start_time < current_datetime).count()
  num_future_shows = db.session.query(Show.artist_id, Show.start_time).filter(Show.artist_id == artist_id).filter(Show.start_time > current_datetime).count()

  return render_template('pages/show_artist.html', artist=artist_data, past_shows=past_shows,
  future_shows=future_shows, num_past=num_past_shows, num_future=num_future_shows)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  #Artist details as entered in the form
  artist_name = request.form.get('name')
  artist_city = request.form.get('city')
  artist_state = request.form.get('state')
  artist_phone = request.form.get('phone')
  artist_genres = ','.join(request.form.getlist('genres'))
  artist_fb_link = request.form.get('facebook_link')
  artist_image = request.form.get('image_link')
  artist_website = request.form.get('website')
  seeking_venue = True if request.form.get('seeking_venue') == 'y' else False
  seeking_description = request.form.get('seeking_description')

  data = {}
  error = False

  #Try to add the data to the database
  try:
      artist = Artist(name=artist_name, city=artist_city, state=artist_state,
      phone=artist_phone, genres=artist_genres, facebook_link=artist_fb_link,
      image_link=artist_image, website=artist_website, seeking_venue=seeking_venue,
      seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
      data['name'] = artist.name
  #If there's an error, rollback the session
  except:
      db.session.rollback()
      error = True
  #Close the connection either way
  finally:
      db.session.close()
  #If an error occurred, flash an error message
  if error:
      flash('An error occurred and the venue was not listed. Please try again.')
  #If there was no error, alert the user the venue was listed
  if not error:
      # on successful db insert, flash success
      flash('Artist ' + data['name'] + ' was successfully listed!')

  # TODO: modify data to be the data object returned from db insertion
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows.
  data = db.session.query(Show.artist_id, Show.venue_id, Show.start_time,
  Artist.name, Artist.image_link , Venue.name).join(Artist).join(Venue).all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  show_venue = request.form.get('venue_id')
  show_artist = request.form.get('artist_id')
  show_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%d %H:%M:%S')

  error = False

  #Try to add the data to the database
  try:
      show = Show(venue_id=show_venue, artist_id=show_artist,
      start_time=show_time)
      db.session.add(show)
      db.session.commit()
  #If there's an error, rollback the session
  except Exception as e:
      db.session.rollback()
      error = True
      print(e)
  #Close the connection either way
  finally:
      db.session.close()
  #If an error occurred, flash an error message
  if error:
      flash('An error occurred and the show was not listed. Please try again.')
  #If there was no error, alert the user the venue was listed
  if not error:
      # on successful db insert, flash success
      flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
