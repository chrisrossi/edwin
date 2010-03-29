function ajax_success(data) {
    if ('image_src' in data) {
        // Reload transformed image
        var src = data['image_src'];
        var width = data['width'];
        var height = data['height'];
        var img = $('.photo img').get(0);

        img.width = width;
        img.height = height;
        img.src = src;

        delete data['image_src'];
        delete data['width'];
        delete data['height'];
    }

    for (name in data) {
        if (name == 'actions') {
            actions = data[name];
            show_actions();
            continue;
        }
        var element = $('.field#' + name);
        element.removeClass('empty_field').html(data[name]);
        decorate_field(element);
    }
}

function ajax_error(request, status, error) {
    // XXX This doesn't seem to get called for timeouts.  jQuery bug?
    ajax_error("Error: " + status + ": " + error);
}

function submit_dynamic(form) {
    jQuery.ajax({
        success: ajax_success,
        error: ajax_error,
        data: $(form).serialize(),
        dataType: 'json',
    })
}

function make_input(fields, element) {
    var field = fields[element.id];
    var handler = function(event){
        var orig_element = $(this).data('orig_element');
        var empty = $(this).data('empty');
        $(this).replaceWith(orig_element);
        if (empty) {
            orig_element.html('');
        }
        decorate_field(orig_element);
        orig_element.removeClass('hover_field');
        if (orig_element.attr('edit_value')) {
            orig_element.attr('edit_value', this.value);
        }
        submit_dynamic(this);
    };
    var value = $(element).html().trim();
    var edit_value = $(element).attr('edit_value');
    var empty = $(element).data('empty');
    if (empty) {
        value = '';
    }
    else if (edit_value) {
        value = edit_value;
    }
    var form = field['factory'](field, value)
        .submit(handler)
        .children()
        .attr('class', $(element).attr('class'))
        .attr('id', $(element).attr('id'))
        .addClass('dynamic_field')
        .removeClass('empty_field')
        .change(handler)
        .blur(handler);
    form.data('orig_element', $(element))
        .data('empty', empty);
    $(element).replaceWith(form);
    var input = form[0];
    input.focus();
}

function make_text_input(field, value) {
    return $('<form><input></form>')
        .children()
        .attr('name', field['name'])
        .attr('value', value)
        .end();
}

function escape_tags(value) {
    return value.split("&").join("&amp;").split( "<").
        join("&lt;").split(">").join("&gt;");
}

function make_textarea_input(field, value) {
    return $('<form><textarea rows="5" cols="40"></textarea></form>')
        .children()
        .attr('name', field['name'])
        .html(escape_tags(value))
        .end();
}

function decorate_fields(fields) {
    $('.field').each(
        function(){
            decorate_field($(this));
        }
    );
}

function decorate_field(field) {
    var id = field.attr('id');
    if (!(id in fields)) {
        return;
    }

    field.hover(
        // Show outline when hovering
        function() {
            $(this).addClass('hover_field');
        },
        function() {
            $(this).removeClass('hover_field');
        }
    ).click(
        // Convert to dynamic input field when clicked
        function() {
            make_input(fields, this);
        }
    );

    // Make sure empty fields are visible
    empty = ! field.html().trim();
    field.data('empty', empty);
    var metadata = fields[id];
    if (empty) {
        field.addClass('empty_field').html(metadata['label']);
    }
}

function do_action(name) {
    jQuery.ajax({
        success: ajax_success,
        data: {action: name},
        dataType: 'json'
    });
}

function show_actions() {
    var div = $('#actions').html('');
    for (var i in actions) {
        var action = actions[i];
        var anchor = $('<a/>')
            .text(action['title'])
            .attr('action', action['name'])
            .addClass('action')
            .click(function() {
               do_action($(this).attr('action'));
            });
        if ('href' in action) {
            anchor.attr('href', action['href']);
        }
        else {
            anchor.attr('href', '#');
        }
        anchor.appendTo(div).wrap('<nobr/>');
    }
}
