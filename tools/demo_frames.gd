extends SceneTree
## Offline export only. No demo scene runs this script.

func _initialize() -> void:
	var target := ProjectSettings.globalize_path("res://demo/media/")
	DirAccess.make_dir_recursive_absolute(target)
	var cast := {}
	for file in DirAccess.get_files_at("res://assets/cast"):
		if file.get_extension() != "tres": continue
		var frames := load("res://assets/cast/" + file) as SpriteFrames
		if not frames: quit(1); return
		var rows := {}
		var id := file.get_basename()
		for action in frames.get_animation_names():
			var tex := frames.get_frame_texture(action, 0)
			if tex.get_width() < 250:
				push_error("Native frames not imported for " + id + "/" + String(action)); quit(1); return
			var durations := []
			var urls := []
			var folder := "frames/" + id + "/" + String(action)
			if DirAccess.make_dir_recursive_absolute(target.path_join(folder)) != OK: quit(1); return
			for i in frames.get_frame_count(action):
				durations.append(frames.get_frame_duration(action, i))
				var source := frames.get_frame_texture(action, i).resource_path
				var url := folder + "/%02d.png" % (i + 1)
				# Copy exactly the lossless texture referenced by Godot, not its filtered rendering.
				if source.get_extension() != "png" or DirAccess.copy_absolute(ProjectSettings.globalize_path(source), target.path_join(url)) != OK:
					push_error("Cannot export frame: " + source); quit(1); return
				urls.append(url)
			rows[action] = {"w":tex.get_width(), "h":tex.get_height(), "fps":frames.get_animation_speed(action), "durations":durations, "urls":urls}
		cast[id] = rows
	if cast.size() != 12: push_error("Expected all twelve cast resources"); quit(1); return
	var output := FileAccess.open(target.path_join("cast.js"), FileAccess.WRITE)
	if not output: quit(1); return
	output.store_string("const CAST=" + JSON.stringify(cast) + ";\n")
	quit()
