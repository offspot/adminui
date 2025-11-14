// matches polyfill
this.Element && function(ElementPrototype) {
        ElementPrototype.matches = ElementPrototype.matches ||
        ElementPrototype.matchesSelector ||
        ElementPrototype.webkitMatchesSelector ||
        ElementPrototype.msMatchesSelector ||
        function(selector) {
                var node = this, nodes = (node.parentNode || node.document).querySelectorAll(selector), i = -1;
                while (nodes[++i] && nodes[i] != node);
                return !!nodes[i];
        }
}(Element.prototype);
// closest polyfill
this.Element && function(ElementPrototype) {
        ElementPrototype.closest = ElementPrototype.closest ||
        function(selector) {
                var el = this;
                while (el.matches && !el.matches(selector)) el = el.parentNode;
                return el.matches ? el : null;
        }
}(Element.prototype);

// helper for enabling IE 8 event bindings
function addEvent(el, type, handler) {
        if (el.attachEvent) el.attachEvent('on'+type, handler); else el.addEventListener(type, handler);
}

function hasClass(el, className) {
    return el.classList ? el.classList.contains(className) : new RegExp('\\b'+ className+'\\b').test(el.className);
}

function addClass(el, className) {
    if (el.classList) el.classList.add(className);
    else if (!hasClass(el, className)) el.className += ' ' + className;
}

function removeClass(el, className) {
    if (el.classList) el.classList.remove(className);
    else el.className = el.className.replace(new RegExp('\\b'+ className+'\\b', 'g'), '');
}

function toggleClass(el, className) {
    console.log('toggleClass for ', el, className);
    if (hasClass(el, className))
        removeClass(el, className);
    else
        addClass(el, className);
}

// live binding helper using matchesSelector
function live(selector, event, callback, context) {
        addEvent(context || document, event, function(e) {
                var found, el = e.target || e.srcElement;
                while (el && el.matches && el !== context && !(found = el.matches(selector))) el = el.parentElement;
                if (found) callback.call(undefined, el, e);
        });
}


/* form mgmt */
function onResetButtonClicked(el, evt) {
    evt.preventDefault();
    el.form.reset();
    // hidePassphraseOnOpenWifi();
    const fields = el.form.querySelectorAll('.changed');
    Array.from(fields).forEach(field => {
      removeClass(field, 'changed');
    });
}
function onChangedField(el, evt) {
addClass(el, 'changed')
}
function manuallyValidateFormOnSubmit(form, event) {
if (!form.checkValidity()) {
  event.preventDefault()
  event.stopPropagation()
}
addClass(form, 'was-validated');
}
