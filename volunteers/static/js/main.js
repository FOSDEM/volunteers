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
	//var div = document.getElementById("container");
	//div.innerHTML = div.innerHTML + "<br>screen width: " + document.documentElement.clientWidth;
	/* for mobile browsing */
	if ( document.documentElement.clientWidth <= 1000 ) {
		/* hide second intro and the <br> on the main page */
		$(".intro span:eq(1)").hide();
		$(".intro span:eq(1)").next().hide();
		/* collapse and open menu */
		$("span.menu-button").on('click', function(e) {
			var elem = $('#nav1');
			if (elem.is(":visible")) elem.hide('fast');
			else elem.show('fast');
			e.stopPropagation();
		});
		/* collapse menu when other activity */
		$(window).scroll(function() {
		    $('#nav1').hide('fast');
		});
		$(window).click(function() {
			$('#nav1').hide('fast');
		});
		/* when in user schedule view */
		if ($('legend.task_list .avatar_large').length != 0) {
			/* rename title */
			var avatar = $('legend.task_list .avatar_large').remove();
			$('h2.content-title').html($('legend.task_list').text().trim().replace("\n", "<br>"));
			$('legend.task_list').html(avatar);
		/* when in task list view */
		} else if ($("legend.task_list").text().indexOf("tasks") > -1) {
			/* when logged in */
			if ($("a[title='View schedule']").length != 0) {
				/* restyle links */
				var link = $("a[title='View schedule']").remove();
				$('h2.content-title').append(" ").append($("<small style='font-size: 0.3em;'>").html(link));
				/* move "change in profile" to next line */
				link = $("legend.task_list span a:eq(0)").remove();
				$("legend.task_list span:eq(0)").html(link);
			}
			/* collapse tasks */
			$("table.task_list tbody tr:not(.category,.day)").hide();
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
		/* when in talk list view */
		} else if ($("legend.talk_list").length != 0) {
			/* add space before submit button */
			$("form.task_list fieldset:last").append("<br>");
			/* open talks when clicked */
			$("legend.talk_list").on('click', function() {
				var elem = $(this).next();
				if (elem.is(":visible")) elem.hide('fast');
				else elem.show('fast');
			});
		/* when in task schedule view */
		} else if ($("form[action^='/task_schedule_csv/']").length != 0) {
			/* add space before and after export CSV button */
			$("form[action^='/task_schedule_csv/']").prepend("<br>").append("<br>");
		/* when in edit profile views */
		} else if ($("h2.content-title").text().indexOf("Account » ") > -1) {
			$("#content-container form fieldset legend:eq(0)").hide();
		}
	}
});