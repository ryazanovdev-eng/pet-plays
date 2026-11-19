extends SceneTree
## M3 presentation-state regression, on an already imported working copy:
## .\tools\godot.cmd -Headless --fixed-fps 60 --script res://tools/check_arena_states.gd
## Exit: 0 pass, 1 failed assertions/load, 2 scene files not built yet.
## Tests the instanced tree, not .tscn text. No imports, captures or writes.

const VIEWS := ["arena", "arena_edge", "arena_wave", "level_up", "shop"]
const SCREEN := Rect2(0, 0, 1280, 720)
# Original minimap perimeter + five paths at 1280x720. Quantized screen
# coordinates, sorted by curve contents (not by authoring names/tree order).
const MAP_PATHS := "648228a5d03eed11cdb0367c7df5ef0783fb6cfb87e2523182ddf7abeadc8cd9"
var failures := 0
var view := ""
var ui: Array[CanvasItem] = []
var actors: Array[AnimatedSprite2D] = []

func _initialize() -> void:
	run.call_deferred()

func expect(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		printerr("FAIL [%s] %s" % [view, message])

func run() -> void:
	var missing := PackedStringArray()
	for id: String in VIEWS:
		var path := "res://game/%s.tscn" % id
		if not FileAccess.file_exists(path):
			missing.append(path)
	for id: String in VIEWS:
		view = id
		var before := failures
		var path := "res://game/%s.tscn" % id
		if path in missing:
			continue
		var err := change_scene_to_file(path)
		expect(err == OK, "cannot load scene: " + error_string(err))
		if err != OK:
			continue
		await scene_changed
		await process_frame
		await process_frame
		expect(root.get_visible_rect().size.is_equal_approx(SCREEN.size), "expected 1280x720 viewport")
		collect()
		var dressing := current_scene.find_child("GroundDressing", true, false) as Node2D
		expect(dressing != null and dressing.is_visible_in_tree() and dressing.get_child_count() > 0, "missing ground dressing in shared arena")
		match id:
			"arena", "arena_edge", "arena_wave":
				check_battle(id == "arena_wave")
			"level_up":
				check_cards()
				await check_frozen()
			"shop":
				check_shop()
		print("%s: %s" % [id, "PASS" if before == failures else "FAIL"])
	if not missing.is_empty():
		printerr("NOT RUN: missing scenes: ", ", ".join(missing))
	var status := 1 if failures else (2 if not missing.is_empty() else 0)
	print("Arena states QA: ", ["PASS", "FAIL (%d)" % failures, "INCOMPLETE"][status])
	quit(status)

func bounds(n: CanvasItem) -> Rect2:
	var local := Rect2()
	if n is Control:
		local = Rect2(Vector2.ZERO, n.size)
	elif n is Sprite2D and n.texture:
		local = n.get_rect()
	elif n is Line2D and not n.points.is_empty():
		local = Rect2(n.points[0], Vector2.ZERO)
		for p: Vector2 in n.points:
			local = local.expand(p)
		local = local.grow(n.width * 0.5)
	return n.get_global_transform_with_canvas() * local

func collect() -> void:
	ui.clear()
	actors.clear()
	for n: CanvasItem in current_scene.find_children("*", "CanvasItem", true, false):
		var layer := n.get_canvas_layer_node()
		if n is AnimatedSprite2D and not layer:
			actors.append(n) # Include offscreen and hidden actors; empty means no encounter.
		if not layer or not layer.visible or not n.is_visible_in_tree() or n.self_modulate.a <= 0:
			continue
		var ancestor := n
		while ancestor and ancestor.modulate.a > 0:
			ancestor = ancestor.get_parent() as CanvasItem
		if not ancestor and SCREEN.intersects(bounds(n)):
			ui.append(n)

func artwork(n: CanvasItem) -> String:
	var tex: Texture2D
	if n is TextureRect or n is Sprite2D:
		tex = n.texture
	elif n is TextureProgressBar:
		tex = n.texture_progress
	while tex is AtlasTexture:
		tex = tex.atlas
	return tex.resource_path.get_file() if tex else ""

func art_nodes(pattern: String) -> Array[CanvasItem]:
	var found: Array[CanvasItem] = []
	for n in ui:
		if artwork(n).match(pattern):
			found.append(n)
	return found

func one_art(pattern: String) -> CanvasItem:
	var found := art_nodes(pattern)
	expect(found.size() == 1, "expected one visible %s, found %d" % [pattern, found.size()])
	return found[0] if found.size() == 1 else null

# Text must be present in the picture, not just declared in a resource.
func labels_in(area: Rect2) -> String:
	var words := PackedStringArray()
	for n in ui:
		if n is Label and area.has_point(bounds(n).get_center()):
			words.append(n.text.strip_edges().to_lower())
	return "\n".join(words)

func matches(text: String, pattern: String) -> bool:
	return RegEx.create_from_string(pattern).search(text) != null

func cast_id(a: AnimatedSprite2D) -> String:
	return a.sprite_frames.resource_path.get_file().get_basename() if a.sprite_frames else ""

func check_battle(normal: bool) -> void:
	var bosses := PackedStringArray()
	var regular := 0
	for a in actors:
		var id := cast_id(a)
		if id.begins_with("boss_"):
			bosses.append(id)
		elif id.begins_with("skeleton_") or id.begins_with("ghost_") or id.begins_with("zombie_"):
			if a.is_visible_in_tree():
				regular += 1
	var right := Rect2(850, 0, 430, 170)
	var labels := labels_in(SCREEN)
	expect(matches(labels, "волна\\s*%d\\s*/\\s*5" % (2 if normal else 3)), "wrong wave number")
	expect(not matches(labels, "(?i)\\b(xp|exp|опыт[а-я]*)\\b"), "visible XP label")
	# Catch the former *unlabelled* XP track/fill (as well as a renamed Range).
	for n in ui:
		if (n is Line2D or n is Range or n is ColorRect or n is Sprite2D or n is TextureRect) and Rect2(125, 78, 210, 35).has_point(bounds(n).get_center()) and bounds(n).size.y < 32:
			expect(false, "unexpected track in hero XP slot: " + str(n.get_path()))
	var right_bars: Array[Range] = []
	for n in ui:
		if n is Range and right.has_point(bounds(n).get_center()):
			right_bars.append(n)
	if normal:
		expect(bosses.is_empty(), "boss still instanced in ordinary wave: " + str(bosses))
		expect(right_bars.is_empty(), "boss health bar visible on ordinary wave")
		for n in ui:
			var art := artwork(n)
			expect(not ("rotten_giant" in art or "bone_king" in art or art in ["empty_frame.png", "red_fill.png"]), "boss HUD on ordinary wave: " + art)
		var counter := RegEx.create_from_string("осталось\\s+врагов\\s*:\\s*(\\d+)").search(labels)
		expect(regular == 10 and counter != null and counter.get_string(1).to_int() == regular, "counter must match all ten ordinary enemies (including those offscreen); observed %d enemies; labels: %s" % [regular, labels])
	else:
		expect(bosses == PackedStringArray(["boss_rotten_giant"]), "expected wave 3 rotten giant, found " + str(bosses))
		var portrait := one_art("rotten_giant_empty_frame.png")
		expect(art_nodes("bone_king_*.png").is_empty(), "another boss portrait/health layer visible")
		if portrait:
			expect(right.has_point(bounds(portrait).get_center()), "boss portrait outside boss HUD")
		expect(right_bars.size() == 1, "missing/duplicate boss health bar")
		for bar in right_bars:
			expect(bar.ratio > 0 and artwork(bar) == "rotten_giant_full_red_overlay.png", "wrong or empty boss fill")
			if portrait:
				expect(bounds(portrait).intersects(bounds(bar)), "boss portrait/frame separated from fill")
		expect(not matches(labels_in(right), "[0-9]"), "numeric text in boss HUD: " + labels_in(right))
	check_minimap()

func check_minimap() -> void:
	var frame := one_art("minimap_empty_frame.png")
	var plate := one_art("currency_bones_panel.png")
	if not frame or not plate:
		return
	var map := bounds(frame)
	var bones := bounds(plate)
	expect(map.get_center().distance_to(Vector2(1196, 631)) <= 1 and map.size.distance_to(frame.texture.get_size() * 0.39) <= 1, "minimap moved/resized: " + str(map))
	expect(SCREEN.encloses(bones) and bones.end.x <= map.position.x + 1 and map.position.x - bones.end.x < map.size.x and absf(bones.get_center().y - map.get_center().y) <= map.size.y * 0.5, "bones must be beside (left of) minimap: " + str(bones))
	expect(matches(labels_in(bones), "(?m)^\\d+$"), "bone plate lacks numeric balance")
	var curves := PackedStringArray()
	for n in ui:
		if n is Line2D and map.has_point(bounds(n).get_center()):
			var coords := PackedStringArray()
			for p: Vector2 in n.points:
				var screen_pos := n.get_global_transform_with_canvas() * p
				coords.append(str(roundi(screen_pos.x)))
				coords.append(str(roundi(screen_pos.y)))
			curves.append(" ".join(coords))
	curves.sort()
	expect(";".join(curves).sha256_text() == MAP_PATHS, "minimap route/perimeter differs from previous edition (%d paths)" % curves.size())

func check_cards() -> void:
	var cards := art_nodes("card_upgrade_*_blank.png")
	expect(cards.size() == 3, "expected three visible level-up cards; got %d" % cards.size())
	expect(matches(labels_in(SCREEN), "выберите[^\\n]*улучшение"), "no visible upgrade prompt")
	var kinds := PackedStringArray()
	var seen: Array[Rect2] = []
	for card in cards:
		var box := bounds(card)
		expect(SCREEN.encloses(box), "card extends beyond viewport")
		for other in seen:
			expect(not box.intersects(other), "overlapping level-up cards")
		seen.append(box)
		var caption := labels_in(box)
		expect(not matches(caption, "(?m)^[123]$"), "unwanted ordinal on upgrade card")
		for pair: Array in [["скорост", "\\+10\\s*%", "winged_boot.png"], ["(?:здоров|живуч|макс|hp)", "\\+20\\b", "ruby_heart.png"], ["(?:урон|сил[аы])", "\\+15\\s*%", "knight_blade.png"]]:
			if matches(caption, pair[0]) and matches(caption, pair[1]):
				kinds.append(pair[0])
				var icon := one_art(pair[2])
				if icon:
					expect(box.has_point(bounds(icon).get_center()), "wrong card for " + str(pair[2]))
				break
	kinds.sort()
	expect(kinds.size() == 3 and kinds[0] != kinds[1] and kinds[1] != kinds[2], "each card needs its own stat and bonus: speed 10%, max HP 20, damage 15%")

func check_frozen() -> void:
	var camera := root.get_camera_2d()
	var enemy_on_screen := false
	for a in actors:
		if a.is_visible_in_tree() and SCREEN.has_point(a.get_global_transform_with_canvas().origin) and cast_id(a) != "frog_knight":
			enemy_on_screen = true
	expect(camera != null and enemy_on_screen, "level-up needs a visible battle background and active camera")
	var initial := motion_sample()
	for i in 30:
		await process_frame
		if motion_sample() != initial:
			expect(false, "background moved or animation progressed at sample %d/30" % (i + 1))
			return

func motion_sample() -> Array:
	var sample := [root.canvas_transform]
	for n: Node2D in current_scene.find_children("*", "Node2D", true, false):
		if n.get_canvas_layer_node():
			continue # The modal overlay is not part of the paused world.
		sample.append([n.get_instance_id(), n.global_transform, n.visible, n.modulate])
		if n is AnimatedSprite2D:
			sample.append([n.animation, n.frame, n.frame_progress])
		elif n is Sprite2D:
			sample.append([n.texture, n.frame])
	return sample

func check_shop() -> void:
	var cast := PackedStringArray()
	for a in actors:
		cast.append(cast_id(a))
	expect(cast == PackedStringArray(["frog_knight"]), "cleared court should contain just the hero, found " + str(cast))
	# Two ledger rows. Pair visible prices with the nearest product title by
	# vertical distance. Exclude +15 HP in the description and the HUD balance.
	var titles := {}
	for n in ui:
		if n is Label:
			for product: String in ["отвар", "тотем"]:
				if product in n.text.to_lower():
					titles[product] = bounds(n).get_center()
	expect(titles.size() == 2, "missing visible product names: " + str(titles.keys()))
	if titles.size() != 2:
		return
	var half_row := absf(titles["отвар"].y - titles["тотем"].y) / 2.0
	for product: String in titles:
		var title: Vector2 = titles[product]
		var price := 15 if product == "отвар" else 25
		var found := false
		for n in ui:
			if not n is Label:
				continue
			var center := bounds(n).get_center()
			if center.x > title.x and absf(center.y - title.y) < half_row:
				if matches(n.text.to_lower().strip_edges(), "^(?:цена\\s*[:·]?\\s*)?%d(?:\\s*кост[а-я]*)?$" % price):
					found = true
		expect(found, "no visible %d-bone price in row '%s'" % [price, product])
