from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required
from app import db
from app.inventory import bp
from app.inventory.forms import CarForm, CarSearchForm, CarImageForm
from app.models.car import Car, CarImage
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

@bp.route('/list')
@login_required
def list_cars():
    form = CarSearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Create base query
    query = Car.query
    
    # Apply filters if provided in URL
    make = request.args.get('make')
    model = request.args.get('model')
    min_year = request.args.get('min_year')
    max_year = request.args.get('max_year')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    max_mileage = request.args.get('max_mileage')
    status = request.args.get('status')
    new_or_used = request.args.get('new_or_used')
    body_style = request.args.get('body_style')
    
    if make:
        query = query.filter(Car.make.ilike(f'%{make}%'))
        form.make.data = make
    
    if model:
        query = query.filter(Car.model.ilike(f'%{model}%'))
        form.model.data = model
        
    if min_year:
        query = query.filter(Car.year >= int(min_year))
        form.min_year.data = int(min_year)
        
    if max_year:
        query = query.filter(Car.year <= int(max_year))
        form.max_year.data = int(max_year)
        
    if min_price:
        query = query.filter(Car.price >= float(min_price))
        form.min_price.data = float(min_price)
        
    if max_price:
        query = query.filter(Car.price <= float(max_price))
        form.max_price.data = float(max_price)
        
    if max_mileage:
        query = query.filter(Car.mileage <= int(max_mileage))
        form.max_mileage.data = int(max_mileage)
        
    if status:
        query = query.filter(Car.status == status)
        form.status.data = status
        
    if new_or_used:
        query = query.filter(Car.new_or_used == new_or_used)
        form.new_or_used.data = new_or_used
        
    if body_style:
        query = query.filter(Car.body_style == body_style)
        form.body_style.data = body_style
    
    # Order by newest first
    cars = query.order_by(Car.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    
    return render_template('inventory/list.html', title='Vehicle Inventory', 
                           cars=cars, form=form)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_car():
    form = CarForm()
    if form.validate_on_submit():
        car = Car(
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            trim=form.trim.data,
            color=form.color.data,
            price=form.price.data,
            mileage=form.mileage.data,
            vin=form.vin.data,
            status=form.status.data,
            description=form.description.data,
            features=form.features.data,
            new_or_used=form.new_or_used.data,
            body_style=form.body_style.data,
            transmission=form.transmission.data,
            fuel_type=form.fuel_type.data
        )
        db.session.add(car)
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            for image_file in form.images.data:
                if image_file.filename:
                    filename = secure_filename(image_file.filename)
                    # Generate a unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cars', str(car.id))
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                    
                    # Save the file
                    file_path = os.path.join(upload_dir, unique_filename)
                    image_file.save(file_path)
                    
                    # Create the image record
                    car_image = CarImage(
                        car_id=car.id,
                        url=f"/uploads/cars/{car.id}/{unique_filename}",
                        is_primary=False  # Set the first image as primary later
                    )
                    db.session.add(car_image)
            
            # Set the first image as primary if no primary image exists
            if not CarImage.query.filter_by(car_id=car.id, is_primary=True).first():
                first_image = CarImage.query.filter_by(car_id=car.id).first()
                if first_image:
                    first_image.is_primary = True
            
            db.session.commit()
        
        flash('Vehicle added successfully!')
        return redirect(url_for('inventory.view_car', car_id=car.id))
    
    return render_template('inventory/create.html', title='Add Vehicle', form=form)

@bp.route('/<int:car_id>')
@login_required
def view_car(car_id):
    car = Car.query.get_or_404(car_id)
    images = CarImage.query.filter_by(car_id=car_id).all()
    primary_image = CarImage.query.filter_by(car_id=car_id, is_primary=True).first()
    
    return render_template('inventory/view.html', title=f'{car.year} {car.make} {car.model}',
                           car=car, images=images, primary_image=primary_image)

@bp.route('/edit/<int:car_id>', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    form = CarForm()
    
    if form.validate_on_submit():
        car.make = form.make.data
        car.model = form.model.data
        car.year = form.year.data
        car.trim = form.trim.data
        car.color = form.color.data
        car.price = form.price.data
        car.mileage = form.mileage.data
        car.vin = form.vin.data
        car.status = form.status.data
        car.description = form.description.data
        car.features = form.features.data
        car.new_or_used = form.new_or_used.data
        car.body_style = form.body_style.data
        car.transmission = form.transmission.data
        car.fuel_type = form.fuel_type.data
        car.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            for image_file in form.images.data:
                if image_file.filename:
                    filename = secure_filename(image_file.filename)
                    # Generate a unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cars', str(car.id))
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                    
                    # Save the file
                    file_path = os.path.join(upload_dir, unique_filename)
                    image_file.save(file_path)
                    
                    # Create the image record
                    car_image = CarImage(
                        car_id=car.id,
                        url=f"/uploads/cars/{car.id}/{unique_filename}",
                        is_primary=False
                    )
                    db.session.add(car_image)
            
            # Set the first image as primary if no primary image exists
            if not CarImage.query.filter_by(car_id=car.id, is_primary=True).first():
                first_image = CarImage.query.filter_by(car_id=car.id).first()
                if first_image:
                    first_image.is_primary = True
            
            db.session.commit()
        
        flash('Vehicle updated successfully!')
        return redirect(url_for('inventory.view_car', car_id=car.id))
    
    elif request.method == 'GET':
        form.make.data = car.make
        form.model.data = car.model
        form.year.data = car.year
        form.trim.data = car.trim
        form.color.data = car.color
        form.price.data = car.price
        form.mileage.data = car.mileage
        form.vin.data = car.vin
        form.status.data = car.status
        form.description.data = car.description
        form.features.data = car.features
        form.new_or_used.data = car.new_or_used
        form.body_style.data = car.body_style
        form.transmission.data = car.transmission
        form.fuel_type.data = car.fuel_type
    
    images = CarImage.query.filter_by(car_id=car_id).all()
    return render_template('inventory/edit.html', title='Edit Vehicle', 
                           form=form, car=car, images=images)

@bp.route('/<int:car_id>/images', methods=['GET', 'POST'])
@login_required
def manage_images(car_id):
    car = Car.query.get_or_404(car_id)
    form = CarImageForm()
    
    if form.validate_on_submit():
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cars', str(car.id))
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save the file
        file_path = os.path.join(upload_dir, unique_filename)
        image_file.save(file_path)
        
        # If this is set as primary, unset any existing primary images
        is_primary = form.is_primary.data == '1'
        if is_primary:
            existing_primary = CarImage.query.filter_by(car_id=car.id, is_primary=True).all()
            for img in existing_primary:
                img.is_primary = False
        
        # Create the image record
        car_image = CarImage(
            car_id=car.id,
            url=f"/uploads/cars/{car.id}/{unique_filename}",
            is_primary=is_primary
        )
        db.session.add(car_image)
        db.session.commit()
        
        flash('Image uploaded successfully!')
        return redirect(url_for('inventory.manage_images', car_id=car.id))
    
    images = CarImage.query.filter_by(car_id=car_id).all()
    return render_template('inventory/images.html', title='Manage Vehicle Images', 
                           form=form, car=car, images=images)

@bp.route('/image/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(image_id):
    image = CarImage.query.get_or_404(image_id)
    car_id = image.car_id
    
    # If this is the primary image, set another image as primary
    if image.is_primary:
        next_image = CarImage.query.filter(CarImage.car_id == car_id, CarImage.id != image_id).first()
        if next_image:
            next_image.is_primary = True
    
    # Delete the file if it exists
    if image.url and image.url.startswith('/uploads/'):
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.url.replace('/uploads/', ''))
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully!')
    return redirect(url_for('inventory.manage_images', car_id=car_id))

@bp.route('/image/<int:image_id>/set-primary', methods=['POST'])
@login_required
def set_primary_image(image_id):
    image = CarImage.query.get_or_404(image_id)
    car_id = image.car_id
    
    # Unset any existing primary images
    existing_primary = CarImage.query.filter_by(car_id=car_id, is_primary=True).all()
    for img in existing_primary:
        img.is_primary = False
    
    # Set this image as primary
    image.is_primary = True
    db.session.commit()
    
    flash('Primary image updated successfully!')
    return redirect(url_for('inventory.manage_images', car_id=car_id))

@bp.route('/<int:car_id>/delete', methods=['POST'])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    # Delete all associated images
    images = CarImage.query.filter_by(car_id=car_id).all()
    for image in images:
        if image.url and image.url.startswith('/uploads/'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.url.replace('/uploads/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        db.session.delete(image)
    
    # Delete the car
    db.session.delete(car)
    db.session.commit()
    
    flash('Vehicle deleted successfully!')
    return redirect(url_for('inventory.list_cars'))
