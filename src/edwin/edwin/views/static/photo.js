var fields = {
    'photo_title': {
        'factory': make_text_input,
        'label': 'Title',
        'name': 'title',
    },
    'photo_desc': {
        'factory': make_textarea_input,
        'label': 'Description',
        'name': 'desc',
    }
};

$(document).ready(function(){
    decorate_fields(fields);
});
