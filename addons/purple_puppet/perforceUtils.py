import os
import subprocess

# P4 User data methods


def checkLogged():
    """Check if the user is currently logged in or not

    Returns:
        (bool) : True if the user is logged in. False otherwise

    """
    try:
        subprocess.check_output(["p4", "login", "-s"], shell=True).decode('ascii')
    except:
        return False

    return True


def getP4Port():
    """Get the perforce host configured in the computer.

    Returns:
        (str) : the current perforce host, or localhost otherwise.


    """
    output = subprocess.check_output(["p4", "set", "P4PORT"], shell=True).decode('ascii')
    try:
        server = output.rpartition("=")[-1].rpartition(" ")[0]
    except:
        server = "127.0.0.1:1666"

    return server


def getP4User():
    """Get the perforce user configured in the computer.

    Returns:
        (str) : the current perforce user, or the OS username.


    """
    output = subprocess.check_output(["p4", "set", "P4USER"], shell=True).decode('ascii')
    try:
        user = output.rpartition("=")[-1].rpartition(" ")[0]
    except:
        user = os.getenv("username")

    return user


def getP4Client():
    """Get the perforce client workspace configured in the computer.

    Returns:
        (str) : the current perforce client workspace, or the OS username.


    """
    output = subprocess.check_output(["p4", "set", "P4CLIENT"], shell=True).decode('ascii')
    try:
        client = output.rpartition("=")[-1].rpartition(" ")[0]
    except:
        client = os.getenv("username")

    return client


def getP4UserClients():
    """Return a list of all user client workspaces

    Returns:
        (list, index) : list of all user clients and the index of the current client

    """
    try:
        currentIndex = "0"
        currentClient = getP4Client()
        output = subprocess.check_output(["p4", "clients", "-u", getP4User()], shell=True).decode('ascii')
        clientsList = list()
        for index, line in enumerate(output.split("\n")[:-1]):
            clientName = line.split(" ")[1]
            if clientName == currentClient:
                currentIndex = str(index)
            clientsList.append(
                (str(index), clientName, "")
            )

        return clientsList, currentIndex

    except:
        currentIndex = "0"
        clientsList = [("0", "None", "")]

    return clientsList, currentIndex


# P4 file management methods


def isVersioned(filePath):
    """Check if a file is versioned

    Args:
        filePath (str) : The file to check the status

    Returns:
        (bool) : If the file is versioned or not

    """
    try:
        output = subprocess.check_output(["p4", "have", filePath], shell=True).decode('ascii')
    except:
        return False

    if not output:
        return False

    return True


def isAddMarked(filePath):
    """Check if a file is marked for add

    Args:
        filePath (str) : The file to check if it's marked for add

    Returns:
        (bool) : If the file is marked for add or not

    """
    try:
        output = subprocess.check_output(["p4", "status", filePath], shell=True).decode('ascii')
        for line in output.split("\n"):
            if "- submit change" in line and "to add" in line:
                return True
        return False
    except:
        return False

    return False


def isLatest(filePath):
    """Check if a file is in the latest version

    Args:
        filePath (str) : The file to check if it's in the latest version

    Returns:
        (bool) : If the file is in the latest version or not

    """
    latestFile = subprocess.check_output(["p4", "files", filePath], shell=True).decode('ascii')
    latestVersion = latestFile.partition("#")[-1].partition(" ")[0]
    currentFile = subprocess.check_output(["p4", "have", filePath], shell=True).decode('ascii')
    currentVersion = currentFile.partition("#")[-1].partition(" ")[0]

    if latestVersion != currentVersion:
        return False
    return True


def getLatest(filePath):
    """Get the latest version of the given file.

    Args:
        filePath (str) : The file to get the latest version.

    Returns:
        (bool) : If the latest version was downloaded or not.

    """
    try:
        subprocess.check_output(["p4", "sync", filePath], shell=True)
    except:
        return False

    if isLatest(filePath):
        return True
    return False


def fileStatus(filePath):
    """Check the status of the file in perforce

    Args:
        filePath (str) : The file to check the status

    Returns:
        (str) : Status of the current file

    """
    try:
        # Check if the scene is already checked out by other person
        output = subprocess.check_output(["p4", "opened", "-a", filePath], shell=True).decode('ascii')
    except:
        return ("error", "File not included in your current client.")

    if "by" in output and "@" in output:
        blockedBy = output.rpartition("by ")[-1].rpartition("@")[0]
        return ("blocked", "The file is blocked by: {0}".format(blockedBy))

    return ("free", "")


def addFile(filePath):
    """Add the given file to perforce

    Args:
        filePath (str) : The file to add

    Returns:
        (str) : The checkout result

    """
    try:
        subprocess.check_output(["p4", "reconcile", "-a", filePath], shell=True).decode('ascii')
        return (True, "File marked to add.")
    except:
        return (False, "The file was not marked to add.")


def checkoutFile(filePath):
    """Checkout the given file in perforce

    Args:
        filePath (str) : The file to checkout

    Returns:
        (bool, str) : The checkout result

    """
    try:
        # Check out the scene
        subprocess.check_output(["p4", "edit", filePath], shell=True)
    except Exception as e:
        return (False, "The file was not checked out.")

    return (True, "The file was checked out.")


def submitFile(filePath, description):
    """Submit the given file in perforce

    Args:
        filePath (str) : The file to submit

    Returns:
        (bool) : The submit result

    """
    try:
        subprocess.check_output(["p4", "submit", "-d", "\"" + description + "\"", filePath], shell=True).decode('ascii')
        return True
    except:
        return False


def revertFile(filePath):
    """Revert the given file

    Args:
        filePath (str) : The file to revert

    Returns:
        (bool) : The revert result

    """
    try:
        subprocess.check_output(["p4", "revert", filePath], shell=True).decode('ascii')
        return True
    except:
        return False
