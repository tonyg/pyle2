function installEditRibbon() {
    var ribbonDiv = document.getElementById("edit_ribbon");
    var textArea = document.getElementById("body");

    function insertExample(pluginDesc) {
	var selStart = textArea.selectionStart;
	var selEnd = textArea.selectionEnd;
	var oldValue = textArea.value;

	if (pluginDesc.plugin_category == "spanhandler"
	    && pluginDesc.example_spacing != ""
	    && selStart != selEnd)
	{
	    // replace selection
	    var newValue =
		oldValue.substring(0, selStart) +
		pluginDesc.example_prefix + pluginDesc.example_spacing +
		oldValue.substring(selStart, selEnd) +
		pluginDesc.example_postfix;
	    var pos = newValue.length;
	    newValue = newValue +
		oldValue.substring(selEnd);
	    textArea.value = newValue;
	    textArea.selectionStart = textArea.selectionEnd = pos;
	} else {
	    if (selStart == selEnd) {
		// insert full example
		var newValue =
		    oldValue.substring(0, selStart) +
		    pluginDesc.example_prefix;
		var pos1 = newValue.length;
		newValue = newValue +
		    pluginDesc.example_spacing +
		    pluginDesc.example_template;
		var pos2 = newValue.length;
		newValue = newValue +
		    pluginDesc.example_postfix;
		var pos3 = newValue.length;
		newValue = newValue +
		    oldValue.substring(selEnd);
		textArea.value = newValue;
		if (pos1 == pos2) {
		    textArea.selectionStart = textArea.selectionEnd = pos3;
		} else {
		    textArea.selectionStart = pos1;
		    textArea.selectionEnd = pos2;
		}
	    }
	}
	textArea.focus();
    }

    function addButton(pluginDesc, containerDiv) {
	var e = document.createElement("button");
	e.className = "ribbon_button";
	e.innerHTML = pluginDesc.friendly_name;
	e.onclick = function () { insertExample(pluginDesc); return false; };
	containerDiv.appendChild(e);
    }

    function newContainer() {
	var c = document.createElement("div");
	c.className = "ribbon_button_container";
	ribbonDiv.appendChild(c);
	return c;
    }

    function addPlugins(plugins) {
	var c = newContainer();
	for (var i = 0; i < plugins.length; i++) {
	    addButton(plugins[i], c);
	}
	return c;
    }

    var blocklanguage_container = newContainer();
    var sublanguage_container = addPlugins(pluginDescriptions.sublanguages);
    var spanhandler_container = addPlugins(pluginDescriptions.spanhandlers);

    addButton({friendly_name: "Unnumbered Item",
	       plugin_category: "blockstructure",
	       example_prefix: "\n -",
	       example_spacing: " ",
	       example_template: "unnumbered list item",
	       example_postfix: ""},
	      blocklanguage_container);

    addButton({friendly_name: "Numbered Item",
	       plugin_category: "blockstructure",
	       example_prefix: "\n #",
	       example_spacing: " ",
	       example_template: "numbered list item",
	       example_postfix: ""},
	      blocklanguage_container);

    textArea.selectionStart = textArea.selectionEnd = 0;
}
installEditRibbon();
