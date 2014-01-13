$(document).ready(function() {
	var temp_title = "";
	$("#dialog").dialog({ autoOpen: false });
	/*$(".task-name").click(function() {
		$("#dialog").html(temp_title);
		$("#dialog").dialog("open");
	});*/
	$(".task-volunteers").click(function() {
		$("#dialog").html(temp_title);
		$("#dialog").dialog("open");
	});
	$(".task_list").tooltip({
		items: "[title]",
		content: function() {
			var element = $(this);
			if ( element.is("[title]") ) {
				temp_title = element.attr("title");
				return temp_title;
			}
		}
	});
});