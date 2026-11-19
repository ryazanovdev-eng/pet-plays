extends Node2D

const RIG_PATH := "res://assets/sprites/player_frog/rig_data.json"
const OUT_DIR := "res://docs/art/raw"

var character: Node2D
var skeleton: Skeleton2D
var anim_player: AnimationPlayer
var bones: Dictionary = {}
var parts: Array = []


func _ready() -> void:
	var text := FileAccess.get_file_as_string(RIG_PATH)
	var data: Variant = JSON.parse_string(text)
	if data == null:
		push_error("PROBE: cannot parse " + RIG_PATH)
		get_tree().quit(1)
		return
	_build_background()
	character = Node2D.new()
	character.name = "Character"
	character.position = Vector2(640, 650)
	character.scale = Vector2(1.5, 1.5)
	add_child(character)
	_build_bones(data["bones"])
	_build_parts(data["parts"])
	_build_animations()
	print("PROBE: bones=", bones.size(), " sprites=", parts.size())
	anim_player.play("idle")
	await get_tree().create_timer(0.30).timeout
	await _shot("20261118-frog-rig-idle")
	anim_player.play("walk")
	await get_tree().create_timer(0.30).timeout
	await _shot("20261118-frog-rig-walk")
	anim_player.play("attack")
	await get_tree().create_timer(0.12).timeout
	await _shot("20261118-frog-rig-attack")
	anim_player.play("hurt")
	await get_tree().create_timer(0.10).timeout
	await _shot("20261118-frog-rig-hurt")
	anim_player.play("death")
	await get_tree().create_timer(0.55).timeout
	await _shot("20261118-frog-rig-death")
	anim_player.play("idle")
	character.scale = Vector2(-1.5, 1.5)
	await get_tree().create_timer(0.15).timeout
	await _shot("20261118-frog-rig-flip")
	get_tree().quit()


func _build_background() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#16232B")
	bg.position = Vector2.ZERO
	bg.size = Vector2(1280, 720)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.z_index = -100
	add_child(bg)
	var ground := Polygon2D.new()
	ground.polygon = PackedVector2Array([
		Vector2(240, 610), Vector2(1040, 610), Vector2(1180, 690), Vector2(100, 690)
	])
	ground.color = Color("#3A3B33")
	add_child(ground)
	var label := Label.new()
	label.text = "Frog cutout rig — probe"
	label.position = Vector2(24, 20)
	label.add_theme_font_size_override("font_size", 22)
	add_child(label)


func _build_bones(defs: Array) -> void:
	skeleton = Skeleton2D.new()
	skeleton.name = "Skeleton2D"
	character.add_child(skeleton)
	for d in defs:
		var bone := Bone2D.new()
		bone.name = String(d["name"])
		bone.set_autocalculate_length_and_angle(false)
		bone.position = Vector2(float(d["pos"][0]), float(d["pos"][1]))
		bone.rotation = 0.0
		bone.length = 10.0
		bone.rest = bone.transform
		var parent := ""
		if d["parent"] != null:
			parent = String(d["parent"])
		if parent == "":
			skeleton.add_child(bone)
		else:
			bones[parent].add_child(bone)
		bones[bone.name] = bone


func _build_parts(defs: Array) -> void:
	for d in defs:
		var path := "res://" + String(d["file"])
		var tex: Texture2D = load(path)
		if tex == null:
			push_error("PROBE: missing texture " + path)
			continue
		var spr := Sprite2D.new()
		spr.name = String(d["name"]) + "Sprite"
		spr.texture = tex
		spr.centered = false
		spr.offset = -Vector2(float(d["pivot_px"][0]), float(d["pivot_px"][1]))
		spr.z_as_relative = false
		spr.z_index = int(d["z"])
		var bone: Bone2D = bones[String(d["bone"])]
		bone.add_child(spr)
		parts.append(spr)


func _build_animations() -> void:
	anim_player = AnimationPlayer.new()
	anim_player.name = "AnimationPlayer"
	anim_player.root_node = NodePath("..")
	character.add_child(anim_player)
	var lib := AnimationLibrary.new()

	var idle := _new_anim(1.6, true)
	_keys(idle, "Skeleton2D/torso:rotation", [[0.0, 0.0], [0.8, 0.025], [1.6, 0.0]])
	_keys(idle, "Skeleton2D/torso/head:rotation", [[0.0, 0.0], [0.8, -0.035], [1.6, 0.0]])
	_keys(idle, "Skeleton2D/torso/scarf_01:rotation", [[0.0, 0.0], [0.8, 0.05], [1.6, 0.0]])
	_keys(idle, "Skeleton2D/torso/cloak:rotation", [[0.0, 0.0], [0.8, -0.04], [1.6, 0.0]])
	lib.add_animation("idle", idle)

	var walk := _new_anim(0.6, true)
	_keys(walk, "Skeleton2D/torso/hip_r:rotation", [[0.0, 0.0], [0.15, -0.22], [0.3, 0.0], [0.45, 0.22], [0.6, 0.0]])
	_keys(walk, "Skeleton2D/torso/hip_l:rotation", [[0.0, 0.0], [0.15, 0.22], [0.3, 0.0], [0.45, -0.22], [0.6, 0.0]])
	_keys(walk, "Skeleton2D/torso/shoulder_r:rotation", [[0.0, 0.0], [0.15, 0.10], [0.3, 0.0], [0.45, -0.10], [0.6, 0.0]])
	_keys(walk, "Skeleton2D/torso/shoulder_l:rotation", [[0.0, 0.0], [0.15, -0.10], [0.3, 0.0], [0.45, 0.10], [0.6, 0.0]])
	_keys(walk, "Skeleton2D/torso:rotation", [[0.0, 0.0], [0.3, 0.03], [0.6, 0.0]])
	lib.add_animation("walk", walk)

	var attack := _new_anim(0.3, false)
	_keys(attack, "Skeleton2D/torso/shoulder_r:rotation", [[0.0, 0.0], [0.08, -1.0], [0.18, 0.7], [0.3, 0.0]])
	_keys(attack, "Skeleton2D/torso/shoulder_r/elbow_r:rotation", [[0.0, 0.0], [0.08, -0.3], [0.18, 0.25], [0.3, 0.0]])
	_keys(attack, "Skeleton2D/torso:rotation", [[0.0, 0.0], [0.08, -0.06], [0.18, 0.06], [0.3, 0.0]])
	lib.add_animation("attack", attack)

	var hurt := _new_anim(0.15, false)
	_keys(hurt, "Skeleton2D/torso:rotation", [[0.0, 0.0], [0.07, -0.14], [0.15, 0.0]])
	_keys(hurt, "Skeleton2D/torso/head:rotation", [[0.0, 0.0], [0.07, 0.12], [0.15, 0.0]])
	lib.add_animation("hurt", hurt)

	var death := _new_anim(1.0, false)
	_keys(death, "Skeleton2D/torso:rotation", [[0.0, 0.0], [0.35, -0.8], [1.0, -1.45]])
	_keys(death, "Skeleton2D/torso/head:rotation", [[0.0, 0.0], [0.5, -0.25], [1.0, -0.4]])
	lib.add_animation("death", death)
	anim_player.add_animation_library("", lib)


func _new_anim(length: float, looped: bool) -> Animation:
	var a := Animation.new()
	a.length = length
	a.loop_mode = Animation.LOOP_LINEAR if looped else Animation.LOOP_NONE
	return a


func _keys(anim: Animation, path: String, keys: Array) -> void:
	var idx := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(idx, NodePath(path))
	anim.value_track_set_update_mode(idx, Animation.UPDATE_CONTINUOUS)
	for k in keys:
		anim.track_insert_key(idx, float(k[0]), float(k[1]))


func _shot(name: String) -> void:
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	var path := OUT_DIR + "/" + name + ".png"
	var err := img.save_png(path)
	print("PROBE_SHOT ", path, " err=", err)
