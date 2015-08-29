import sys
from p4_hlir.main import HLIR
from p4_hlir.hlir.p4_headers import p4_field_list
from p4_hlir.hlir.p4_headers import p4_field_list_calculation
from p4_hlir.hlir.p4_imperatives import P4_READ
from p4_hlir.hlir.p4_imperatives import P4_WRITE
from p4_hlir.hlir.p4_imperatives import P4_READ_WRITE
from sets import Set

# Pretty print primitive action invocation
def pretty_print_primitive(action_primitive_invocation):
  # Check that this is really an action primitive and
  # doesn't net any other actions within it.
  action_primitive = action_primitive_invocation[0]
  assert(action_primitive.flat_call_sequence == [])

  # Get actual parameters for this invocation
  actual_parameters= action_primitive_invocation[1]
  return action_primitive.name + "(" + ",".join([str(p) for p in actual_parameters]) + ");";

# Get set of variables from an actual parameter passed
# to a P4 action primitive
# In most cases, this just calls str() on the actual parameter object
# With field_list_calc and field_lists, we need to recurse one level
# deeper and return a set
def gen_parameter_set(actual_parameter):
  var_set = Set();
  if (isinstance(actual_parameter, p4_field_list_calculation)):
    # Per the grammar on page 14 of the P4 spec, a field list calculation
    # can reference multiple field lists as inputs
    for field_list in actual_parameter.input:
      for field in field_list.fields:
        var_set.add(str(field))
  elif (isinstance(actual_parameter, p4_field_list)):
    for field in actual_parameter.fields:
      var_set.add(str(field))
  else :
    var_set.add(str(actual_parameter))
  return var_set

# Get set of variables for a particular invocation
# of an action primitive
def get_var_set(action_primitive_invocation, var_type):
  # Store all reads for the action_primitive_invocation
  var_set = Set()

  # Check that this is really an action primitive and
  # doesn't net any other actions within it.
  action_primitive = action_primitive_invocation[0]
  assert(action_primitive.flat_call_sequence == [])

  # Get actual parameters for this invocation
  actual_parameters= action_primitive_invocation[1]

  # Get formal parameters for this action primitive
  formal_parameters = action_primitive.signature

  # <= because the formal_parameters might have optional
  # arguments that aren't supplied (such as mask in modify_field)
  assert(len(actual_parameters) <= len(formal_parameters))

  # Collect either read or write sets
  for i in range(0, len(actual_parameters)):
    # field list and field list calc need special care,
    # But both have to be READ objects
    if (isinstance(actual_parameters[i], p4_field_list_calculation)):
      assert(action_primitive.signature_flags[formal_parameters[i]]['access'] == P4_READ)
    if (isinstance(actual_parameters[i], p4_field_list)):
      assert(action_primitive.signature_flags[formal_parameters[i]]['access'] == P4_READ)

    if (var_type == "read"):
      if (((action_primitive.signature_flags[formal_parameters[i]])['access'] == P4_READ) or
          ((action_primitive.signature_flags[formal_parameters[i]])['access'] == P4_READ_WRITE)):
        var_set.update(gen_parameter_set(actual_parameters[i]))
    elif (var_type == "write"):
      if (((action_primitive.signature_flags[formal_parameters[i]])['access'] == P4_WRITE) or
          ((action_primitive.signature_flags[formal_parameters[i]])['access'] == P4_READ_WRITE)):
        var_set.update(gen_parameter_set(actual_parameters[i]))
    else :
      assert(False)

  return var_set

def analyze_read_write_sets(complex_action):
  # Maintain read and write sets for each primitive action in a complex_action
  read_sets  = []
  write_sets = []
  for action_primitive in complex_action.flat_call_sequence:
    read_sets += [(action_primitive, get_var_set(action_primitive, "read"))]
    write_sets += [(action_primitive, get_var_set(action_primitive, "write"))]

  # Check for pairwise intersection of these sets
  print >> sys.stderr, "complex_action is ", complex_action.name,
  flag = False;
  for i in range(0, len(complex_action.flat_call_sequence)):
    for j in range(i, len(complex_action.flat_call_sequence)):
      if (((read_sets[i][1] & write_sets[j][1]) != Set([])) or (write_sets[i][1] & read_sets[j][1])) :
        print >> sys.stderr, "Flagging intersection between action_primitives "
        print >> sys.stderr, "@ location: ", i, pretty_print_primitive(complex_action.flat_call_sequence[i])
        print >> sys.stderr, "@ location: ", j, pretty_print_primitive(complex_action.flat_call_sequence[j])
        flag = True
  if (flag == False):
    print >> sys.stderr, " no read/write intersection",
  print >> sys.stderr

if __name__ == "__main__":
  # Build HLIR
  h = HLIR(sys.argv[1])
  h.build()
  actions = h.p4_actions

  # Accumulate all complex actions (user-defined actions)
  complex_actions = []
  for a in actions:
    if (actions[a].flat_call_sequence != []):
      complex_actions += [actions[a]]

  for complex_action in complex_actions:
    analyze_read_write_sets(complex_action)
