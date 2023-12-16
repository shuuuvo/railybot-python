import datetime



def move(state,prediction_dicts):
    for key in prediction_dicts.keys():
        origin = prediction_dicts[key]['or']
        if origin == state:
            yield prediction_dicts[key]['ds']


def is_goal(state, state_goal):
    return list(state) == list(state_goal)


def dfs_rec(path, goal_state, max_depth,pred):
    # First evaluates if the state is th goal, if its the goal, returns the path and the yield count
    if is_goal(path[-1], goal_state):
        return path
    # Second, it evaluates if the level is the last one to look on. if it is, returns None as no path has been found
    elif max_depth == 0:
        return None
    else:
        # Last, if we haven't found a goal and, we still have levels to look on, start searching on the possible moves
        for nextState in move(path[-1],pred):
            # adds one to the yield count
            # Checks if the next states is not contain in the current path, we dont want to end up in a loop.
            # If it does, add the state to the current path and run again dfs on the current state.
            if nextState not in path:
                nextPath = path + [nextState]
                solution = dfs_rec(nextPath, goal_state, max_depth - 1,pred)
                # if a solution is found, solution should not be None and the code should stop
                if solution is not None:
                    return solution
    # If none of the conditions is satisfied and the code gets to the next line, no solution has been found
    return None


def iddfs(start_state, goal_state, max_depth,pred):
    """
    Main method. starts the search
    :param start_state: First state
    :param goal_state: State to get to
    :param max_depth: maximum level to look up
    :return: returns the path from de start state to the goal state (None if its not found) and the number of yields,
    """
    # Iniciates a count variable in 0
    # Iterates until the max depth parameter given by the user,
    for i in range(max_depth):

        path = dfs_rec([start_state], goal_state, i,pred)
        # if a solution is found, solution should not be None and the code should stop iterating
        if path is not None:
            return path
    return None



def get_time(start_state,end_state,prediction_dicts,delay_minutes):

    path = iddfs(start_state, end_state, 100,prediction_dicts)

    tuples = [path[i] + '-' + path[i + 1] for i in range(0, len(path) - 1)]

    time = datetime.datetime.now()
    time_lapsed = 0
    for model_id in tuples:
        model = prediction_dicts[model_id]['model']
        if isinstance(model, str):
            time_lapsed += int(model)
        else:
            time_lapsed += int(model.predict([[0, 0]])[0])

    return (time + datetime.timedelta(seconds=time_lapsed) + datetime.timedelta(minutes=delay_minutes)).time().strftime('%H:%M')


start_state = 'UPWEY'
end_state = 'SWAY'