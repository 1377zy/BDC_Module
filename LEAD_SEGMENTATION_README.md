# Lead Segmentation Feature

## Overview
The Lead Segmentation feature allows users to create and manage segments of leads based on various criteria. Segments can be used to target specific groups of leads for marketing campaigns, follow-ups, or other actions.

## Features Implemented

### 1. Segmentation Based on Interests
- Create segments based on vehicle interests (make, model, year, type)
- Filter leads by interest level and other interest-related attributes

### 2. Budget-Based Segmentation
- Segment leads by budget range (min/max amount)
- Filter by payment preferences (down payment, monthly payment)
- Group leads by financing options

### 3. Timeline-to-Purchase Segmentation
- Segment leads by purchase timeline (immediate, 30 days, 60 days, etc.)
- Filter by urgency level
- Group by specific purchase dates

### 4. Custom Segmentation Criteria
- Create custom fields for segmentation
- Define criteria using various operators (equals, contains, greater than, etc.)
- Combine multiple criteria with AND/OR logic

### 5. Segment Management Interface
- View all segments in a centralized dashboard
- Create, edit, and delete segments
- Preview leads in a segment before saving
- Export segment leads to CSV

## Implementation Details

### Files Created/Modified

1. **Models**
   - `app/models.py`: Added models for Segment, SegmentCriteria, LeadInterest, LeadBudget, LeadTimeline, CustomSegmentField, and CustomSegmentValue

2. **Routes**
   - `app/routes/segmentation_routes.py`: Contains all routes for the segmentation feature
   - `app/routes/__init__.py`: Registration of segmentation routes

3. **Templates**
   - `app/templates/leads/segmentation.html`: Main segmentation dashboard
   - `app/templates/leads/segment_editor.html`: Create/edit segment form
   - `app/templates/leads/view_segment.html`: View segment details and leads
   - `app/templates/leads/segment_field_options.html`: Field options for segment criteria
   - `app/templates/leads/segment_leads_table.html`: Table for displaying segment leads
   - `app/templates/leads/custom_segment_fields.html`: Manage custom segment fields

4. **Integration**
   - `integrate_segmentation.py`: Instructions for integrating the segmentation routes with the main application

### Key Functionality

#### Dynamic vs. Static Segments
- **Dynamic Segments**: Automatically update based on criteria
- **Static Segments**: Manually managed lists of leads

#### Segment Criteria Types
- Basic lead information (name, email, phone, status, etc.)
- Interest-based criteria (vehicle make, model, year, etc.)
- Budget-based criteria (price range, payment preferences)
- Timeline-based criteria (purchase timeline, urgency)
- Custom field criteria (user-defined fields)

#### Custom Fields
- Create custom fields for leads
- Define field types (text, number, date, boolean, selection)
- Use custom fields in segment criteria

## Integration Guide

To integrate the lead segmentation feature with the main application:

1. Ensure all models are properly defined in `app/models.py`
2. Register the segmentation blueprint with the Flask app:
   ```python
   from app.routes.segmentation_routes import segmentation_bp
   app.register_blueprint(segmentation_bp)
   ```
3. Alternatively, use the routes registration function:
   ```python
   from app.routes import register_all_routes
   register_all_routes(app)
   ```

See `integrate_segmentation.py` for detailed integration instructions.

## Usage Guide

### Creating a Segment
1. Navigate to the Segmentation dashboard
2. Click "Create Segment"
3. Select segment type (interest, budget, timeline, custom)
4. Enter segment name and description
5. Define segment criteria
6. Choose criteria logic (AND/OR)
7. Save the segment

### Managing Custom Fields
1. Navigate to the Custom Fields page
2. Add new custom fields with appropriate types
3. These fields will be available for use in segment criteria

### Working with Segments
- View segment details and leads
- Export segment leads to CSV
- For static segments, manually add/remove leads
- For dynamic segments, update the segment to refresh the lead list based on criteria

## Next Steps
1. Test all segmentation functionality thoroughly
2. Integrate with email marketing features
3. Add segment analytics
4. Create segment-based workflow triggers
