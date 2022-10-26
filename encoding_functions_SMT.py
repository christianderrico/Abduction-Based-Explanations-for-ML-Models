import sys

from pysat.examples.hitman import Hitman
from pysmt.shortcuts import Symbol, Implies, Iff, TRUE, LE, Real, FALSE, GE, And, Solver, Equals, Minus, Times, Int, GT, \
    Or, Plus, Not, ExactlyOne
from pysmt.typing import REAL, INT, BOOL

from encoding_utils_functions import generate_variables, get_variables_names


def SMT_indicator_constraints(y, s):
    name = "Z_" + '_'.join(("" + str(y)).split("_")[1:-2])

    z = Symbol(name, INT)

    constraint = []
    constraint.append(Implies(Equals(z, Int(1)), LE(y, Real(0))))
    constraint.append(Implies(Equals(z, Int(0)), LE(s, Real(0))))
    constraint.append(ExactlyOne(Equals(z, Int(0)), Equals(z, Int(1))))

    constraint.append(GE(y, Real(0)))
    constraint.append(GE(s, Real(0)))

    return constraint


def print_solver_assertion(fname, solver):
    original_stdout = sys.stdout  # Save a reference to the original standard output

    with open(fname, "a") as f:
        sys.stdout = f  # Change the standard output to the file we created.
        for a in solver.assertions:
            print("Assertion: ", a.serialize())

        sys.stdout = original_stdout  # Reset the standard output to its original value


def cancel_file(fname):
    file = open(fname, "w")
    file.close()


def copy_solver(solver):
    s = Solver(name="z3")
    s.add_assertions(solver.assertions)
    return s


def define_formula_SMT(categorical_ids, A, b):

    n_of_layers = len(A)

    formula_terms = []
    solver = Solver(name="z3")
    all_vars = {}

    for n_of_layer in range(n_of_layers):

        number_of_vars = len(A[n_of_layer][0])

        variables_names = generate_variables(n_of_layer, categorical_ids, number_of_vars)
        if all_vars == [] or not all(item in all_vars.keys() for item in variables_names):
            to_add = {v_name: Symbol(v_name, REAL) for v_name in variables_names}
            all_vars.update(to_add)
            variables = list(to_add.values())
        else:
            variables = [v[1] for v in all_vars.items() if v[0] in variables_names]

        categorical_boundaries = [ExactlyOne(Equals(v, Real(0)), Equals(v, Real(1))) for v in
                       [all_vars[k] for k in all_vars.keys() if "_type_B" in k and all_vars[k] in variables]]

        solver.add_assertions(categorical_boundaries)

        n_vars = len(variables)
        n_outputs = len(A[n_of_layer])

        if n_of_layer == 0:
            inputs = variables.copy()

        for id_output in range(n_outputs):
            formula_terms.clear()
            for id_var in range(n_vars):
                coeff = Real(float(A[n_of_layer][id_output][id_var]))
                new_term = Times(coeff, variables[id_var])
                formula_terms.append(new_term)

            constant_term = Real(float(b[n_of_layer][id_output]))
            formula_terms.append(constant_term)

            formula = Plus(formula_terms)

            support_variables = get_variables_names(id_output, n_of_layer)
            y = Symbol(support_variables[0], REAL)
            all_vars[support_variables[0]] = y

            s = None
            if len(support_variables) == n_of_layers:
                s = Symbol(support_variables[1], REAL)
                all_vars[support_variables[1]] = s

            second_term = Minus(y, s) if s else y
            formula = Equals(formula, second_term)

            solver.add_assertion(formula)

            if n_of_layer + 1 < n_of_layers:
                ic = SMT_indicator_constraints(y, s)
                for constraint in ic:
                    solver.add_assertion(constraint)

    return solver, inputs


def freeze_input_and_output_SMT(pb, inputs, outputs):

    input_vars, input_values = inputs
    output_vars, output_values = outputs

    hypos = get_hypos_SMT(input_vars, input_values)
    freeze_output_SMT(pb, output_vars, output_values)

    return hypos


def get_hypos_SMT(input_vars, input_value):
    return [Equals(input_vars[i], Real(float(input_value[i]))) for i in range(len(input_vars))]


def set_bound(var):
    return And(LE(var, Int(1)), GE(var, Int(0)))


def freeze_output_SMT(solver, output_vars, output_value):

    output_vars = [Symbol(v, typename=REAL) for v in output_vars]
    output_id = output_value.index(1)

    disj = []
    for i in range(len(output_value)):
        if i != output_id:
            disj.append(GT(output_vars[i], output_vars[output_id]))

    solver.add_assertion(And(disj))


def minimal_expl_SMT(solver, hypos):

    fname = "encoded_with_smt_solver"
    cancel_file(fname)
    print_solver_assertion(fname, solver)

    if solver.solve(hypos):
        print('no implication!')
        print(solver.get_model())
        sys.exit(1)

    rhypos = compute_minimal_SMT(solver, hypos)

    return rhypos

def smallest_expl_SMT(oracle, hypos):

    def get_var_name_and_value(h):
        var_name, value_in_string = ''.join([c for c in h.__str__() if c not in ['(', ')']]).replace(" ", "").split("=")
        var = Symbol(var_name, REAL)
        value = float(value_in_string)
        return (var, var_name), value

    fname = "encoded_with_smt_solver"
    cancel_file(fname)
    print_solver_assertion(fname, oracle)

    with Hitman(bootstrap_with=[[i for i in range(len(hypos))]]) as hitman:

        # computing unit-size MCSes
        for i, hypo in enumerate(hypos):

            if oracle.solve(hypos[:i] + hypos[(i + 1):]):
                print("ipo: ", hypo)
                hitman.hit([i])

        iters = 0

        i = 0

        while True:
            hset = hitman.get()

            iters += 1

            print('iter: ', iters)
            print('cand: ', hset)

            if oracle.solve([hypos[i] for i in hset]):

                to_hit = []
                satisfied, falsified = [], []

                #free vars are not fixed vars: C \ h
                free_variables = list(set(range(len(hypos))).difference(set(hset)))
                print("Free vars: ", free_variables)

                model = oracle.get_model()

                for h in free_variables:
                    hypo = hypos[h]
                    (var, var_name), exp = get_var_name_and_value(hypo)
                    print("Var: ", var)
                    print("Value: ", exp)

                    if "_C" in var_name:
                        true_val = float(model.get_py_value(var))
                        print("True value UP: ", true_val)
                        add = not (exp - 0.001 <= true_val <= exp + 0.001)
                    else:
                        true_val = int(model.get_py_value(var))
                        print("True value DOWN: ", true_val)
                        add = exp != true_val

                    print("Is falsified? ", add)
                    if add:
                        falsified.append(h)
                    else:
                        hset.append(h)

                #falsified + satisfied = C \ h
                print("Unsatisfied: ", falsified)
                print("hset: ", satisfied)

                for u in falsified:
                    print("hset now: ", hset)
                    print("u: ", u)
                    #to_add = [u] + hset
                    #print("To add: ", to_add)

                    if oracle.solve([hypos[i] for i in hset] + [hypos[h]]):
                        hset.append(u)
                    else:
                        to_hit.append(u)

                print("coex: ", to_hit)
                hitman.hit(to_hit)
            else:
                print("return ", hset)
                return hset

def compute_minimal_SMT(solver, hypos):

    rhypos = hypos.copy()

    i = 0

    while i < len(rhypos):

        to_test = rhypos[:i] + rhypos[(i + 1):]

        if solver.solve(to_test):
            print("solution find")
            i += 1
        else:
            print("solution not find")
            rhypos = to_test

    return rhypos