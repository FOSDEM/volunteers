$(document).ready(function() {
	$( document ).tooltip({
		items: "img, [data-geo], [title]",
		content: function() {
			var element = $(this);
			if ( element.is("[title]") ) {
				return element.attr("title");
			}
		}
	});
});