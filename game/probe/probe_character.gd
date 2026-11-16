extends Node3D


func _ready() -> void:
	var model: Node = get_node_or_null("Model")
	print("PROBE: scene ready, model = ", model)
	if model:
		print("PROBE: model children = ", model.get_child_count())
		for child in model.get_children():
			print("PROBE: child = ", child.name, " (", child.get_class(), ")")
