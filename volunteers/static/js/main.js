$(document).ready(function() {
	var div = document.getElementById("container");
	div.innerHTML = div.innerHTML + "<br>screen width: " + document.documentElement.clientWidth;
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
	$(".talk-volunteers").click(function() {
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
	$(".talk_list").tooltip({
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