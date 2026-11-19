extends SceneTree
## Offline integration test; run after import, never attach to a scene:
## .\tools\godot.cmd -Headless --script res://tools/check_arena_views.gd

const VIEWS := ["res://game/arena.tscn", "res://game/arena_edge.tscn"]

var failures := 0
var layout_path := ""
var layout_transform := Transform2D.IDENTITY

func _initialize() -> void:
	run.call_deferred()

func fail(message: String) -> void:
	failures += 1
	printerr("FAIL [arena QA] ", message)

func run() -> void:
	var frames: Array[Rect2] = []
	for path: String in VIEWS:
		var err := change_scene_to_file(path)
		if err != OK:
			fail("%s: %s" % [path, error_string(err)])
			continue
		await scene_changed
		# Let queued shape updates reach the server before querying its space.
		await physics_frame
		await physics_frame
		var camera := root.get_camera_2d()
		if camera == null or not current_scene.is_ancestor_of(camera):
			fail(path + ": no current Camera2D in this scene")
			continue
		# The canvas transform includes zoom, limits and offset; node.position does not.
		var frame := root.canvas_transform.affine_inverse() * root.get_visible_rect()
		frames.append(frame)
		print("%s: camera=%s, visible world=%s" % [path, frame.get_center(), frame])
		check_world(path, frame)
	if frames.size() == 2:
		var displacement := (frames[1].get_center() - frames[0].get_center()).abs()
		var screens := displacement / frames[0].size.max(frames[1].size)
		print("Camera separation (viewport widths, heights): ", screens)
		if screens.length() < 1.0:
			fail("Camera separation is less than one normalized viewport")
	print("Arena QA: ", "PASS" if failures == 0 else "FAIL (%d)" % failures)
	quit(0 if failures == 0 else 1)

func check_world(path: String, frame: Rect2) -> void:
	# Compare authored scene sources, not World2D RIDs: sequential scenes can
	# occupy the same viewport physics space without sharing a layout at all.
	var maps: Array[Node2D] = []
	for child in current_scene.get_children():
		if child is Node2D and not child.scene_file_path.is_empty():
			if child.find_children("*", "StaticBody2D", true, false).size() > 0:
				maps.append(child)
	if maps.size() != 1:
		fail("%s: expected one instanced layout containing the perimeter, found %d" % [path, maps.size()])
		return
	var world := maps[0]
	if world.find_children("*", "Sprite2D", true, false).is_empty() and world.find_children("*", "TileMapLayer", true, false).is_empty():
		fail(path + ": shared scene contains physics but no cemetery artwork")
	if path == VIEWS[0]:
		layout_path = world.scene_file_path
		layout_transform = world.global_transform
	elif world.scene_file_path != layout_path:
		fail("Different layout sources: %s vs %s" % [layout_path, world.scene_file_path])
	elif not world.global_transform.is_equal_approx(layout_transform):
		fail(path + ": layout moved between shots; centers are not in the same coordinates")
	print("  Layout: ", world.scene_file_path)
	check_perimeter(world, path, frame)

func check_perimeter(world: Node2D, path: String, frame: Rect2) -> void:
	# The envelope only sets ray length. The six perimeter segments are not a rectangle.
	var bounds := Rect2()
	for node in world.find_children("*", "StaticBody2D", true, false):
		var body := node as StaticBody2D
		for owner_id in body.get_shape_owners():
			var transform := body.global_transform * body.shape_owner_get_transform(owner_id)
			for i in body.shape_owner_get_shape_count(owner_id):
				var box := transform * body.shape_owner_get_shape(owner_id, i).get_rect()
				bounds = box if bounds == Rect2() else bounds.merge(box)
	if not bounds.has_area():
		fail(path + ": no measurable wall shapes")
		return
	if not bounds.encloses(frame) and path == VIEWS[0]:
		fail(path + ": central viewport does not fit inside the map bounds " + str(bounds))
	if not bounds.has_point(frame.get_center()):
		fail(path + ": camera center is outside the map bounds " + str(bounds))
	var edge_visible := false
	for direction: Vector2 in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		var origin := frame.get_center()
		var ray := PhysicsRayQueryParameters2D.create(origin, origin + direction * (bounds.size.length() + 1.0))
		var hit := world.get_world_2d().direct_space_state.intersect_ray(ray)
		if hit.is_empty() or not (hit.collider is StaticBody2D) or not world.is_ancestor_of(hit.collider):
			fail("%s: no layout wall on ray %s -> %s" % [path, ray.from, ray.to])
			continue
		if hit.normal.dot(direction) >= -0.5:
			fail("%s: unexpected wall normal %s on ray %s" % [path, hit.normal, direction])
		var coordinate: float = hit.position.dot(direction)
		var projected_center := frame.get_center().dot(direction)
		if absf(projected_center - coordinate) <= frame.size.dot(direction.abs()) / 2.0:
			edge_visible = true
		print("  hit ", direction, " at ", hit.position, ": ", world.get_path_to(hit.collider))
	if edge_visible != (path == VIEWS[1]):
		fail(path + ": physical perimeter should intersect only the edge viewport")
