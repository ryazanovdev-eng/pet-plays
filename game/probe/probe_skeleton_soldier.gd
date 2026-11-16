extends Node3D

@onready var model: Node3D = $Model


func _ready() -> void:
	print("PROBE: skeleton model = ", model)
	var player := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if player:
		var names := player.get_animation_list()
		print("PROBE: animations = ", names)
		if not names.is_empty():
			var anim := player.get_animation(names[0])
			anim.loop_mode = Animation.LOOP_LINEAR
			player.play(names[0])
			print("PROBE: playing = ", names[0], " (loop)")
	else:
		print("PROBE: AnimationPlayer not found")
