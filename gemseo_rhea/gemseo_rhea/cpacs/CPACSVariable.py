

class CPACSVariable:
    """
    Define CPACS variable that corresponds to a xml XPath
    """

    def __init__(self, xpath_template, list_id_template):
        self.__xpath_template = xpath_template
        self.__list_id_template = list_id_template

    @property
    def xpath_template(self):
        return self.__xpath_template

    @property
    def list_id_template(self):
        return self.__list_id_template

    def get_xpath(self, list_id_values):
        """
        Return the real xpath, replacing template variable.

        Args:
            list_id_values (list of str): the list of values for template variables

        Returns:
            string: the real xpath
        """
        if len(list_id_values) != len(self.__list_id_template):
            raise ValueError("The number of values in list_id_values"
                             + " should be {} while it is {}.".format(str(len(self.__list_id_template)),
                                                                      str(len(list_id_values))))

        return self.__xpath_template.format(
            **dict(zip(self.__list_id_template, list_id_values)))
