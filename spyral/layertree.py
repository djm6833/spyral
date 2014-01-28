from weakref import ref as _wref

"""
Important concepts:
    Relative Depth Chain - a list of numbers indicating the current relative position of this layer. If we had four layers like so:
        Scene -> View : [0,0]
        Scene -> View -> "top" : [0, 0, 0]
        Scene -> View -> "top" -> View : [0, 0, 1, 0]
        Scene -> View -> "bottom" : [0, 0, 1]
    Absolute Position Value
        A number representing a Relative Depth Chain collapsed into a single integer (or long, possibly)
"""

class LayerTree(object):
    MAX_LAYERS = 40
    def __init__(self, scene):
        """
        Starts keeping track of the entity as a child of this view.
        
        :param scene: The scene that owns this LayerTree.
        :type scene: Scene (not a weakref).
        """
        self.layers = {_wref(scene) : []}
        self.child_views = {_wref(scene) : []}
        self.layer_location = {_wref(scene) : [0]}
        self.scene = _wref(scene)
        self.tree_height = {_wref(scene) : 1}
        self._precompute_positions()
    
    def remove_view(self, view):
        """
        Removes all references to this view; it must have previously been added to the LayerTree.
        
        :param view: the View to remove
        :type view: View (not a weakref)
        """
        view = _wref(view)
        del self.tree_height[view]
        del self.layers[view]
        self.child_views[view()._parent].remove(view)
        del self.child_views[view]
        self._precompute_positions()
        
    def add_view(self, view):
        """
        Starts keeping track of this view in the LayerTree.
        
        :param view: the new View to add
        :type view: View (not a weakref)
        """
        parent = _wref(view._parent)
        view = _wref(view)
        self.layers[view] = []
        self.child_views[view] = []
        self.child_views[parent].append(view)
        self.tree_height[view] = 1
        if len(self.child_views[parent]) == 1:
            self.tree_height[parent] += 1
            while parent != self.scene:
                parent = _wref(parent()._parent)
                self.tree_height[parent] += 1
        self._precompute_positions()
        
    def set_view_layer(self, view, layer):
        """
        Set the layer that this View is on. Behavior is undefined if that layer does not exist in the parent, so make sure you eventually add that layer to the parent.
        
        :param view: the view have its layer set
        :type view: View (not a weakref)
        :param layer: the name of the layer on the parent
        :type layer: string
        """
        view.layer = layer
        self._precompute_positions()
        
    def set_view_layers(self, view, layers):
        """
        Set the layers that will be available for this view or scene.
        
        :param view: the view have its layer set
        :type view: View (not a weakref) or a Scene (not a weakref)
        :param layers: the name of the layer on the parent
        :type layers: a list of strings
        """
        self.layers[(view)] = list(layers)
        self._precompute_positions()
    
    def _compute_positional_chain(self, chain):
        """
        From a list of numbers indicating the location of the View/layer within the current level, compute an absolute number in base MAX_LAYERS that can quickly and easily compared.
        
        :param chain: The relative positions at this level
        :type chain: a list of numbers
        """
        total = 0
        for index, value in enumerate(chain):
            power = self.maximum_height - index - 1
            total += value * (self.MAX_LAYERS ** power)
        return total
        
    def _precompute_positions(self):
        """
        Runs through the entire LayerTree and calculates an absolute number for each possible view/layer, which can be easily compared.
        """
        self.maximum_height = self.tree_height[self.scene]
        self.layer_location = {}
        self._precompute_position_for_layer(self.scene, [])
        for layer_key, value in self.layer_location.iteritems():
            self.layer_location[layer_key] = self._compute_positional_chain(value)
        
    def _precompute_position_for_layer(self, view, current_position):
        """
        For a given view, and the current depth in the layer heirarchy, compute
        what its relative depth chain should look like. Sets this entry for 
        layer_location to be a list of numbers indicating the relative depth. 
        Note that this is called in a recursive manner to move down the entire 
        LayerTree.
        
        :param view: The current view to explore
        :type view: a weakref to a View!
        :param current_position: The current relative depth chain
        :type current_position: list of numbers
        """
        position = 0
        for position, layer in enumerate(self.layers[view], 1):
            self.layer_location[(view, layer)] = current_position + [position]
        self.layer_location[view] = current_position + [1+position]
        for subview in self.child_views[view]:
            if subview().layer is None:
                new_position = self.layer_location[view]
            else:
                new_position = self.layer_location[(view, subview().layer)]
            self._precompute_position_for_layer(subview, new_position)
    
    def get_layer_position(self, parent, layer):
        """
        For a given layer (and also that layer's parent/owner, since layer 
        alone is ambiguous), identify what the Absolute Position Value is from the precomputed cache, allowing for :above and :below modifiers.
        
        :param parent: The view or scene that has this layer
        :type parent: a View or a Scene (not weakrefs!)
        :param layer: the name of the layer that we're interested in.
        :type layer: string
        """
        parent = _wref(parent)
        s = layer.split(':')
        layer = s[0]
        offset = 0
        if len(s) > 1:
            mod = s[1]
            if mod == 'above':
                offset = 0.5
            if mod == 'below':
                offset = -0.5
        if (parent, layer) in self.layer_location:
            position = self.layer_location[(parent, layer)]
        elif parent in self.layer_location:
            position = self.layer_location[parent]
        else:
            position = self.layer_location[self.scene]
        return position + offset
        
"""
# These should be re-implemented as tests
    
class Scene(object):
    def __str__(self):
        return "Scene"
    __repr__ = __str__
class View(object):
    def __init__(self, scene, name):
        self.parent = self.scene = scene
        self.layer = None
        self.name = name
    def __str__(self):
        return self.name + " - " + str(self.layer)
    __repr__ = __str__
scene = Scene()
view = View(scene, "V#1")
view2 = View(scene, "V#2")
view3 = View(view2, "V#3")
view2_1 = View(view2, "V#2_1")
view4 = View(view3, "V#4")

lt = LayerTree(scene)
lt.set_view_layers(scene, ["bottom", "top"])
lt.add_view(view)
lt.set_view_layer(view, "top")
lt.add_view(view2)
lt.set_view_layer(view2, "bottom")
lt.add_view(view3)
lt.add_view(view2_1)
lt.set_view_layers(view2, ["alpha", "beta", "gamma"])
lt.set_view_layer(view2_1, "beta")
lt.add_view(view4)
lt._precompute_positions()
for name, order in sorted(lt.layer_location.iteritems(), key=lambda x:x[1]):
    print name, order
print "*" * 10
for name, children in lt.child_views.iteritems():
    print name, ":::", map(str, children)
print "*" * 10
"""