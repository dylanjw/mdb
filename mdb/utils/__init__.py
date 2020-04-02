def mutate_merge(*dicts):
    for d in dicts[1:]:
        dicts[0].update(d)
