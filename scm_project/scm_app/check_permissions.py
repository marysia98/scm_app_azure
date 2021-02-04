def is_producer(user):
    return user.groups.filter(name='Producers').exists()

def is_buyer(user):
    return user.groups.filter(name='Buyers').exists()