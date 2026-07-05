# Automatically generated combined Ursina scene
from ursina import *
import random
import keyword
app = Ursina()

# Entity data (for reference)
entities_data = [ { 'Name': 'land',
    'collider': 'box',
    'color': "color.hex('#48f955')",
    'enabled': 'True',
    'model': 'cube',
    'position': '(0.0, -1.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(40.0, 1.0, 40.0)',
    'texture': 'grass',
    'visible': 'True'},
  { 'Name': 'num1',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(1.0, 1.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num1.jpeg',
    'visible': 'True'},
  { 'Name': 'num2',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(2.0, 1.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num2.jpeg',
    'visible': 'True'},
  { 'Name': 'num3',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(1.0, 0.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num3.jpeg',
    'visible': 'True'},
  { 'Name': 'num4',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(2.0, 0.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num4.jpeg',
    'visible': 'True'},
  { 'Name': 'num5',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(3.0, 0.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num5.jpeg',
    'visible': 'True'},
  { 'Name': 'num6',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(1.0, 1.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num6.jpeg',
    'visible': 'True'},
  { 'Name': 'num7',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(2.0, 1.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num7.jpeg',
    'visible': 'True'},
  { 'Name': 'num8',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(1.0, 0.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num8.jpeg',
    'visible': 'True'},
  { 'Name': 'num9',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(2.0, 0.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num9.jpeg',
    'visible': 'True'},
  { 'Name': 'num10',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(3.0, 0.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\num10.jpeg',
    'visible': 'True'},
  { 'Name': 'cadd',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(-1.0, 0.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\cadd.jpeg',
    'visible': 'True'},
  { 'Name': 'cmin',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(-1.0, 0.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\cmin.jpeg',
    'visible': 'True'},
  { 'Name': 'ctim',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(-2.0, 0.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\ctim.jpeg',
    'visible': 'True'},
  { 'Name': 'cdiv',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(-2.0, 0.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\cdiv.jpeg',
    'visible': 'True'},
  { 'Name': 'startcal',
    'collider': 'box',
    'color': 'color.lime',
    'enabled': 'True',
    'model': 'cube',
    'position': '(0.0, 0.0, 2.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'white_cube',
    'visible': 'True'},
  { 'Name': 'copb',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(3.0, 1.0, 1.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\copb.jpeg',
    'visible': 'True'},
  { 'Name': 'cclb',
    'collider': 'box',
    'color': 'color.yellow',
    'enabled': 'True',
    'model': 'cube',
    'position': '(3.0, 1.0, 0.0)',
    'rotation': (0.0, 0.0, 0.0),
    'scale': '(1.0, 1.0, 1.0)',
    'texture': 'assets\\cclb.jpeg',
    'visible': 'True'}]

# Create entities and assign to named variables when possible
for item in entities_data:
    ent = Entity(
        model=item.get('model', 'cube'),
        texture=item.get('texture', None) or None,
        color=eval(item['color']) if isinstance(item['color'], str) else color.white,
        scale=eval(item['scale']) if isinstance(item['scale'], str) else item['scale'],
        position=eval(item['position']) if isinstance(item['position'], str) else item['position'],
        rotation=eval(item['rotation']) if isinstance(item['rotation'], str) else item['rotation'],
        enabled=item.get('enabled', 'True') == 'True',
        visible=item.get('visible', 'True') == 'True',
        collider=item.get('collider', None) or None,
    )
    name = item.get('Name', '')
    if name and name.isidentifier() and not keyword.iskeyword(name):
        globals()[name] = ent

# Scene script
from ursina.prefabs.first_person_controller import FirstPersonController
player = FirstPersonController()
calstr = ""
block_lis = []
calact = {num1:"1", num2:"2", num3:"3",
num4:"4",num5:"5",num6:"6",
num7:"7",num8:"8",num9:"9",
num10:"0",cadd:"+",cmin:"-",
ctim:"*",cdiv:"/",copb:"(",
cclb:")"}
def color_back(entity):
    entity.color = color.yellow
def input(key):
    global calstr, calact, block_lis
    if key == 'left mouse down':
        hit_info=raycast(camera.world_position, camera.forward, distance=5)
        x = 0
        if hit_info.hit and hit_info.entity in calact:
            action = calact[hit_info.entity]
            calstr += action
            hit_info.entity.color = color.red; invoke(color_back, hit_info.entity, delay=0.3)
        elif hit_info.entity == startcal:
            res = eval(calstr)
            for delb in block_lis[:]:
                destroy(delb)
            nl = len(str(int(res)))
            for i in range(nl):
                newblock = Entity(model='cube', color=color.black, texture='white_cube', position=(3-((i*2)-8), 0, -9), collider=None)
                block_lis.append(newblock)
                for ey in range(int(res / (10**(nl-i-1))) - int(res / (10**(nl-i)))*10):
                    newblock = Entity(model='cube', color=color.white, texture='white_cube', position=(3-((i*2)-8), ey+1, -9), collider=None)
                    block_lis.append(newblock)
            calstr = ""

app.run()
