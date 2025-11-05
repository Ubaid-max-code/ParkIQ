from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from controllers.config import Config
from controllers.models import db 
from datetime import datetime , timedelta
from flask import Flask , render_template , request , redirect , url_for , flash , session
from functools import wraps
from controllers.models import db , User , ParkingLot , ParkingSpot , Reservation 
from controllers.config import Config
from flask import send_file

app = Flask(__name__)   
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    from controllers.models import *   
    db.create_all()
    admin= User.query.filter_by(username='ubaid_admin').first()
    if not admin:
        admin = User(username='ubaid_admin', name='Ubaid Rehman', role='admin', password='ubaid123')
        db.session.add(admin)
        db.session.commit()
        print('Admin created')
    
#DECORATOR  
def auth_required(func):
  @wraps(func)
  def inner(*args, **kwargs):
    if 'user_id' not in session:
      return redirect(url_for('login'))
    return func(*args, **kwargs)
  return inner


@app.route('/')
@auth_required
def index():
  return render_template('index.html' , user=User.query.get(session['user_id']))


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@LOGIN AND REGISTER ROUTES#######################################
@app.route('/login', methods=['GET', 'POST'])
def login():

  if request.method == 'POST':
    print("POST request received")

    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if username == '' or password == '':
      flash('Username or password cannot be empty', 'danger')
      return redirect(url_for('login'))

    if not user:
      flash('User does not exist', 'danger')
      return redirect(url_for('login'))
    if not user.check_password(password):
      flash('Wrong password', 'danger')
      return redirect(url_for('login'))

    #Login successful 
    #session stores these
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['is_admin'] = user.is_admin

    if user.role == 'admin':
      return redirect(url_for('admin_dashboard'))
    else: 
      return redirect(url_for('user_dashboard'))
  return render_template('login.html')
    
  
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!PROFILE ROUTE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/profile')
@auth_required  #calling DECORATOR  
def profile():
  return render_template('profile.html', user=User.query.get(session['user_id']))

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
  user = User.query.get(session['user_id'])
  username = request.form.get('username')
  name=request.form.get('name')
  password= request.form.get('new_password')
  cpassword=request.form.get('cpassword')
  if username == '' or password == '' or cpassword == '':
    flash('Username or password cannot be empty')
    return redirect(url_for('profile'))
  if not user.check_password(cpassword):
    flash('Wrong Password')
    return redirect(url_for('profile'))
  if User.query.filter_by(username=username).first() and username != user.username:
    flash('Username already exists')
    return redirect(url_for('profile'))
  user.username = username
  user.name = name
  if password:
    user.password = password
  db.session.commit()
  flash('Profile updated successfully')
  return redirect(url_for('profile'))
  

@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('login'))


####!!!!!!!!!!!!!!!!!!!!!!!!!!!ADMIN DASHBOARD!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

@app.route('/admin/dashboard')
@auth_required
def admin_dashboard():
  if session.get('role')!= 'admin':
    flash('Access denied. Admins only.')
    return redirect(url_for('login'))
  return render_template('admin/admin_dashboard.html')
    


@app.route('/register')
def register():
  return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_post():
  username=request.form.get('username')
  password=request.form.get('password')
  name=request.form.get('name')
  if username == '' or password == '':
    flash('Username or password cannot be empty')
    return redirect(url_for('register'))
  if User.query.filter_by(username=username).first():
    flash('user already exists')
    return redirect(url_for('login'))
  user=User(username=username , password=password ,name=name , role='user')
  db.session.add(user)
  db.session.commit()
  flash('User successfully registered')
  return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


############################################CRUD ROUTES FOR ADMIN############################################
#ADMIN DECORATOR
def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Admins only.')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function 
  
  
#first creating viewing part(all parking lots)
@app.route('/admin/lots')
@admin_required
def view_lots():
    lots = ParkingLot.query.all()
    return render_template('admin/view_lots.html', lots=lots)



def create_spots_for_lot(lot_id, count):
    lot = ParkingLot.query.get(lot_id)
    for i in range(count):
        spot = ParkingSpot(lot_id=lot.lot_id, availability='A', spot_number=str(i + 1))
        db.session.add(spot)
    db.session.commit()

#now doing add operation
@app.route('/admin/lots/add', methods=['GET', 'POST'])
@admin_required
def add_lot():
    if request.method=='POST':
      lot_name = request.form.get('lot_name')
      location = request.form.get('location')
      postal_code = request.form.get('postal_code')
      billing_rate = request.form.get('billing_rate')
      maximum_spots = request.form.get('maximum_spots')

      if not all([lot_name, location, postal_code, billing_rate, maximum_spots]):
        flash('All fields are required', 'danger')
        return redirect(url_for('add_lot'))

      new_lot = ParkingLot(lot_name=lot_name, location=location, postal_code=postal_code, billing_rate=float(billing_rate), maximum_spots=int(maximum_spots))
      db.session.add(new_lot)
      db.session.commit()
      
      create_spots_for_lot(new_lot.lot_id, new_lot.maximum_spots)
      flash('Parking lot added successfully', 'success')
      return redirect(url_for('view_lots'))
    return render_template('admin/add_lot.html')
  
#NOW EDITING PART
@app.route('/admin/lots/edit/<int:lot_id>', methods=['GET', 'POST'])
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        lot.lot_name = request.form.get('lot_name')
        lot.location = request.form.get('location')
        lot.postal_code = request.form.get('postal_code')
        lot.billing_rate = float(request.form.get('billing_rate'))
        lot.maximum_spots = int(request.form.get('maximum_spots'))
        
        if not all([lot.lot_name, lot.location, lot.postal_code, lot.billing_rate, lot.maximum_spots]):
            flash('All fields are required', 'danger')
            return redirect(url_for('edit_lot', lot_id=lot.lot_id))
        db.session.commit()
        flash('Parking lot updated successfully', 'success')
        return redirect(url_for('view_lots'))
    
    return render_template('admin/edit_lot.html', lot=lot)


#delete lots
@app.route('/admin/lots/delete/<int:lot_id>', methods=['GET','POST'])
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted successfully', 'success')
    return redirect(url_for('view_lots'))
  

#####IMPLEMENTING VIEW SPOTS FUNCTIONALITY#####
@app.route('/admin/lots/<int:lot_id>/spots')
@admin_required
def view_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.lot_id).all()
    return render_template('admin/view_spots.html', lot=lot, spots=spots)
  
  
  
######implementing Admin should see a list of all users and their details. (username, spot used etc.)#########
@app.route('/admin/users')
@admin_required
def view_users():
    username = session.get('username')
    current_user = User.query.filter_by(username=username).first()
    users=User.query.all()
    return render_template('admin/view_users.html', user=current_user , users=users)




######MILESTONE 4---USER ###########################################################################################################
@app.route('/user/dashboard')
@auth_required
def user_dashboard():
  if session.get('role')!= 'user':
    flash('Access denied. Users only.')
    return redirect(url_for('login'))
  user_id=session.get('user_id')
  lots=ParkingLot.query.all()
  reservations = Reservation.query.filter_by(user_id=user_id, end_time=None).all()
  return render_template('user/user_dashboard.html', lots=lots , reservations=reservations)


@app.route('/user/lots')
@auth_required
def user_view_lots():
    user_id = session.get('user_id')
    if not user_id:
      flash("Please log in first", "warning")
      return redirect(url_for('login'))
    user = User.query.get(user_id)
    lots = ParkingLot.query.all()
    return render_template('user/view_ulots.html', user=user, lots=lots)


@app.route('/user/lots/<int:lot_id>/spots')
@auth_required
def view_available_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spots = ParkingSpot.query.filter_by(lot_id=lot.lot_id , availability='A').all()
    return render_template('user/view_uspots.html', lot=lot, spots=available_spots)
  
@app.route('/user/lots/<int:lot_id>/reserve')
@auth_required
def auto_reserve(lot_id):
  user_id = session.get('user_id')
  if not user_id:
    flash("Please log in first", "warning")
    return redirect(url_for('login'))
  lot=ParkingLot.query.get_or_404(lot_id)
  spot = ParkingSpot.query.filter_by(lot_id=lot_id, availability='A').first()  #this will find first av_sp
  if not spot:
    flash('No available spots in this lot.', 'danger')
    return redirect(url_for('user_view_lots'))
  reservation = Reservation(user_id=user_id,spot_id=spot.id,start_time=datetime.utcnow(),end_time=None)
  db.session.add(reservation)
  spot.availability= 'U'  # Mark the spot as unavailable
  db.session.commit()
  
  flash(f'Successfully reserved spot ID {spot.id} in {lot.lot_name}', 'success')
  return redirect(url_for('user_dashboard'))


@app.route('/user/reservations/<int:reservation_id>/occupy')
@auth_required
def occupy_spot(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.start_time:
      flash('spot already occupied' , 'warning')
    else:
      reservation.start_time=datetime.now()
      db.session.commit()
      flash('spot occupied successfully')
    return(redirect(url_for('user_dashboard')))
  

@app.route('/user/reservations/<int:reservation_id>/release')
@auth_required
def release_spot(reservation_id): 
  reservation = Reservation.query.get_or_404(reservation_id)
  if not reservation.start_time:
    flash("You must occupy the spot first.", "danger")
    return redirect(url_for('user_dashboard'))  
  elif reservation.end_time:
    flash("Spot already released.", "warning")
    return redirect(url_for('user_dashboard'))  
  else:
    reservation.end_time = datetime.now()
    reservation.parking_spot.availability = 'A'  # Mark the spot as available again 
    # Duration & Billing calculation
    duration = (reservation.end_time - reservation.start_time).total_seconds() / 3600
    reservation.total_duration = round(duration, 2)
    rate = reservation.parking_spot.parking_lot.billing_rate
    reservation.grand_total = round(duration * rate, 2)

    db.session.commit()
    flash("Spot released successfully.", "success")
    return redirect(url_for('user_dashboard'))
  
  
  ###################MILESTONE 5 and 6----#############################################################
@app.route('/user/history')
@auth_required
def user_history():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first", "warning")
        return redirect(url_for('login'))
    
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.start_time.desc()).all()
    return render_template('user/history.html', reservations=reservations)
  


@app.route('/admin/revenue')
@admin_required
def admin_revenue():
  reservations = Reservation.query.order_by(Reservation.start_time.desc()).all()
  total_revenue = sum(r.grand_total for r in reservations if r.grand_total)
    
  return render_template('admin/revenue.html', reservations=reservations, total_revenue=total_revenue)




###########SEARCH FUNCTIONALITY FOR ADMIN#########################
@app.route('/admin/search', methods=['GET', 'POST'])
@admin_required
def admin_search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        if not search_query:
            flash('Please enter a search term', 'warning')
            return redirect(url_for('admin_search'))
        
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
        lots = ParkingLot.query.filter(ParkingLot.lot_name.ilike(f'%{search_query}%')).all()
        spots = ParkingSpot.query.filter(ParkingSpot.spot_number.ilike(f'%{search_query}%')).all()
        reservations = Reservation.query.join(User).join(ParkingSpot).join(ParkingLot).filter(db.or_(User.username.ilike(f"%{search_query}%"),ParkingSpot.spot_number.ilike(f"%{search_query}%"),ParkingLot.lot_name.ilike(f"%{search_query}%"))).order_by(Reservation.start_time.desc()).all()
        return render_template('admin/search_results.html', results=reservations, search_query=search_query)
    
    return render_template('admin/search.html')
  
  
  
  
#@@@@@@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!charts/SUMMARY implementation@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#USING CHART.JS
@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    lots = ParkingLot.query.all()

    pie_labels = []
    pie_data = []

    bar_labels = []
    occupied_data = []
    available_data = []

    for lot in lots:
        total = len(lot.spots)
        occupied = sum(1 for s in lot.spots if not s.availability)
        available = total - occupied

        # Pie chart
        pie_labels.append(lot.lot_name)
        pie_data.append(total)

        # Bar chart
        bar_labels.append(lot.lot_name)
        occupied_data.append(occupied)
        available_data.append(available)

    return render_template('admin/analytics.html',pie_labels=pie_labels,pie_data=pie_data,labels=bar_labels,occupied=occupied_data,available=available_data)

@app.route('/user/analytics')
@auth_required
def user_analytics():
    if session.get('role') != 'user':
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    
    # Fetch all reservations of this user
    reservations = Reservation.query.filter_by(user_id=user_id).all()

    # Count reservations per parking spot
    spot_data = {}
    for res in reservations:
        spot_id = res.parking_spot.id
        spot_label = f"Spot {spot_id} (Lot {res.parking_spot.parking_lot.lot_name})"
        spot_data[spot_label] = spot_data.get(spot_label, 0) + 1

    labels = list(spot_data.keys())
    values = list(spot_data.values())

    return render_template('User/analytics.html', labels=labels, values=values)


if __name__ == '__main__':
    app.run(debug=True)
