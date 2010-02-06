var fields = {
    'title': {
        'factory': make_text_input,
        'label': 'Title',
        'name': 'title',
    },
    'location': {
        'factory': make_text_input,
        'label': 'Location',
        'name': 'location',
    },
    'date': {
        'factory': make_text_input,
        'label': 'Date',
        'name': 'date',
    },
    'desc': {
        'factory': make_textarea_input,
        'label': 'Description',
        'name': 'desc',
    }
};

$(document).ready(function(){
    if (editable) {
        decorate_fields(fields);
        show_actions();
    }
});
