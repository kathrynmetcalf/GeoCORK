def duplicate_entry(header, duplicates):
    strlst = ', '.join(duplicates)
    text = f'''Each entry in {header} must be unique (case insensitive)
                Duplicates: {strlst}'''
    return text

def blank_entry(header):
    text = f'{header} cannot be blank'
    return text

def savepoint_fail(header):
    text = f'Failed to create savepoint for {header}'
    return text

def savepoint_release_fail(header):
    text = f'Failed to release savepoint for {header}'
    return text

def savepoint_rollback_fail(header):
    text = f'Failed to rollback {header}'
    return text

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    pass