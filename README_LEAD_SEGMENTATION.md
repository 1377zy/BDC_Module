# Lead Segmentation Feature

## Overview
The Lead Segmentation feature allows BDC agents and managers to create and manage segments of leads based on various criteria. This helps in organizing leads into meaningful groups for targeted communication and follow-up actions.

## Features
1. **Interest-based Segmentation**: Group leads based on their vehicle interests
2. **Budget-based Segmentation**: Segment leads according to their budget ranges
3. **Timeline-to-Purchase Segmentation**: Categorize leads based on their purchase timeline
4. **Custom Segmentation Criteria**: Create custom fields and criteria for advanced segmentation
5. **Segment Management Interface**: User-friendly interface to create, edit, and delete segments

## Implementation Details

### Models
The following models have been implemented to support lead segmentation:

1. **Segment**: Main model for lead segments
   - Properties: name, description, created_by, is_dynamic
   - Relationships: criteria, leads, creator

2. **SegmentCriteria**: Model for segment criteria
   - Properties: segment_id, field, operator, value

3. **LeadInterest**: Model for tracking lead interests
   - Properties: lead_id, interest_type, interest_value, interest_level

4. **LeadBudget**: Model for tracking lead budget information
   - Properties: lead_id, min_amount, max_amount, preferred_payment_type, down_payment, monthly_payment

5. **LeadTimeline**: Model for tracking lead purchase timeline
   - Properties: lead_id, timeline_type, specific_date, urgency_level, reason

6. **CustomSegmentField**: Model for custom segment fields defined by users
   - Properties: name, display_name, field_type, options, created_by

7. **CustomSegmentValue**: Model for values of custom segment fields for leads
   - Properties: field_id, lead_id, value

### Routes
The segmentation routes are defined in `app/routes/segmentation_routes.py` and include:

1. **Segment List**: View all segments
2. **Create Segment**: Create a new segment
3. **Edit Segment**: Modify an existing segment
4. **Delete Segment**: Remove a segment
5. **View Segment**: View leads in a segment
6. **Add Lead to Segment**: Manually add a lead to a segment
7. **Remove Lead from Segment**: Remove a lead from a segment
8. **Custom Field Management**: Create, edit, and delete custom fields

## Integration Guide

### Blueprint Registration
The segmentation blueprint is registered in the Flask application with the following code:

```python
from app.routes.segmentation_routes import segmentation_bp
app.register_blueprint(segmentation_bp, url_prefix='/leads')
```

### Model Integration
The segmentation models are defined in `app/models_main.py` and are integrated with the Lead model through relationships.

### Usage
1. Access the segmentation features through the `/leads/segments` route
2. Create segments by defining criteria
3. View leads in segments
4. Export segment data for reporting

## Next Steps
1. Implement the frontend templates for the segmentation interface
2. Add segment analytics to track segment performance
3. Integrate segmentation with the email marketing features
4. Add batch operations for segments
