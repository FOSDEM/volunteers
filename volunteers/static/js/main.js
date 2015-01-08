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

	/* debug the screen width */
	var div = document.getElementById("container");
	div.innerHTML = div.innerHTML + "<br>screen width: " + document.documentElement.clientWidth;
	/* for mobile browsing */
	if ( document.documentElement.clientWidth <= 1000 ) {
		/* collapse and open menu */
		$("span.menu-button").on('click', function() {
			var elem = $('#nav1');
			if (elem.is(":visible")) elem.hide('fast');
			else elem.show('fast');
		});
		/* collapse tasks */
		$("table.task_list tbody tr:not(.category)").hide();
		/* open tasks when clicked */
		$("table tbody tr.category").on('click', function() {
			$(this).nextUntil(".row-hide").each(function() {
				if ($(this).is(":visible")) {
					$(this).hide('fast');
				} else {
					$(this).show('fast');
					$(this).css('display', 'block');
				}
			});
		});
		/* open talks when clicked */
		$("legend.talk_list").on('click', function() {
			var elem = $(this).next();
			if (elem.is(":visible")) elem.hide('fast');
			else elem.show('fast');
		});
	}
});