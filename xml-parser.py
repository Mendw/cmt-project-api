import xml.etree.ElementTree as ET
import json
from datetime import date as tdate
from typing import List
from time import sleep


def join(strings: List[str], sep=" "):
    strings = [string.replace(' ', '_') for string in strings]
    return sep.join(
        " ".join(strings).split()
    ).replace('_', ' ') or None


class AbstractParser():
    def __init__(self, path):
        self.root = ET.parse(path).getroot()

    def get_row(self):
        raise NotImplementedError

    def save_to_database(self, row):
        print(row)

    def parse(self):
        for row in self.get_row():
            self.save_to_database(row)


class SemaLmesParser(AbstractParser):
    def get_name(self, record: ET.Element):
        name = record.find('Entity')
        if name is None:
            first_name = record.find('GivenName')
            last_name = record.find('LastName')

            if first_name != None:
                if last_name != None:
                    return "{0} {1}".format(first_name.text, last_name.text)
                return first_name.text
        else:
            name = name.text

        return name

    def get_row(self):
        for record in self.root:
            location = record.find('Country')
            name = self.get_name(record)
            date_of_birth = record.find('DateOfBirth')
            accuracy = None

            if date_of_birth != None:
                dob = date_of_birth.text.split(' or ')[0].split('-')
                accuracy = len(dob)
                date_of_birth = tdate.fromisoformat('-'.join(dob)) if accuracy == 3 else tdate(int(dob[0]), int(
                    dob[1]), 1) if accuracy == 2 else tdate(int(dob[0]), 1, 1) if accuracy == 1 else None

            aliases = record.find('Aliases')
            schedule = record.find('Schedule')

            extra_info = {}
            if aliases != None:
                extra_info['aliases'] = aliases.text

            if schedule != None:
                extra_info['schedule'] = schedule.text

            yield {
                'location': location.text if location != None else None,
                'name': name,
                'dob': date_of_birth,
                'dob-accuracy': accuracy,
                'extra-info': extra_info if extra_info != {} else None,
                'source': "SemaLmes"
            }


class ConsolidatedParser(AbstractParser):
    def get_individual_name(self, individual: ET.Element):
        return join([
            individual.findtext('COUNTRY') or "",
            individual.findtext('SECOND_NAME') or "",
            individual.findtext('THIRD_NAME') or ""
        ])

    def get_individual_location(self, individual: ET.Element):
        location = individual.find('INDIVIDUAL_ADDRESS')
        if location != None:
            return join([
                location.findtext('STREET') or "",
                location.findtext('CITY') or "",
                location.findtext('STATE_PROVINCE') or "",
                location.findtext('ZIP_CODE') or "",
                location.findtext('COUNTRY') or ""
            ])

    def get_individual_dob(self, individual: ET.Element):
        date_of_birth = (None, 0, 0)
        for element in individual.findall('INDIVIDUAL_DATE_OF_BIRTH'):
            datetype = element.findtext('TYPE_OF_DATE')
            score = 2 if datetype == 'EXACT' else 1 if datetype == 'APPROXIMATELY' else 0

            year = element.findtext('YEAR')
            date = element.findtext('DATE')

            if date:
                score *= 3
                resolution = 3
                _ = tdate.fromisoformat('-'.join(date.split('-')[:3]))
            elif year != None:
                resolution = 1
                _ = tdate(int(year), 1, 1)
            else:
                _ = None
                resolution = 0

            if score > date_of_birth[2]:
                date_of_birth = (_, resolution, score)
                if score == 6:
                    break

        return date_of_birth[:2]

    def get_individual_aliases(self, individual: ET.Element):
        return [{
            'name': alias.findtext('ALIAS_NAME'),
            'quality': alias.findtext('QUALITY')
        } for alias in individual.findall('INDIVIDUAL_ALIAS') if alias.findtext('ALIAS_NAME') not in ["", None]] or None

    def get_entity_location(self, entity: ET.Element):
        address = entity.find('ENTITY_ADDRESS')
        return join([
            address.findtext('STREET') or "",
            address.findtext('CITY') or "",
            address.findtext('STATE_PROVINCE') or "",
            address.findtext('ZIP_CODE') or "",
            address.findtext('COUNTRY') or "",
        ])

    def get_entity_aliases(self, entity: ET.Element):
        return [{
            'name': alias.findtext('ALIAS_NAME'),
            'quality': alias.findtext('QUALITY')
        } for alias in entity.findall('ENTITY_ALIAS') if alias.findtext('ALIAS_NAME') not in ["", None]] or None

    def get_row(self):
        individuals = self.root.find('INDIVIDUALS')
        entities = self.root.find('ENTITIES')

        for individual in individuals:
            name = self.get_individual_name(individual)
            location = self.get_individual_location(individual)
            (date_of_birth, accuracy) = self.get_individual_dob(individual)
            aliases = self.get_individual_aliases(individual)
            extra_info = {}

            if aliases != None:
                extra_info['aliases'] = aliases

            yield {
                'location': location,
                'name': name,
                'dob': date_of_birth,
                'dob-accuracy': accuracy,
                'extra-info': extra_info if extra_info != {} else None,
                'source': "Consolidated"
            }

        for entity in entities:
            name = entity.findtext('FIRST_NAME')
            location = self.get_entity_location(entity)
            aliases = self.get_entity_aliases(entity)

            extra_info = {}
            if aliases != None:
                extra_info['aliases'] = aliases

            yield {
                'location': location,
                'name': name,
                'dob': None,
                'extra-info': extra_info if extra_info != {} else None,
                'source': 'Consolidated'
            }


class ConsolidatedListParser(AbstractParser):
    places = {}
    programs = {}

    def get_places(self):
        for element in self.root.findall('place'):
            self.places[element.attrib['ssid']] = join([
                el.text or "" for el in element
            ], ", ")

    def get_programs(self):
        for element in self.root.findall('sanctions-program'):
            program = None
            for el in element.findall('sanctions-set'):
                if el.attrib['lang'] == 'eng':
                    program = (el.text or "", el.attrib['ssid'])
                    break
            if program is None:
                el = element.find('sanctions-set')
                program = (el.text or "", el.attrib['ssid'])
            self.programs[program[1]] = program[0]

    def get_individual_name(self, individual: ET.Element):
        return join([part.findtext('value') or "" for part in individual.findall('./identity/name/name-part')])

    def get_individual_dob(self, individual: ET.Element):
        ymd = individual.find('./identity/day-month-year')
        if ymd == None:
            return (None, 0)

        ymd = ymd.attrib
        year, month, day = (
            int(ymd['year']),
            int(ymd['month']) if 'month' in ymd else None,
            int(ymd['day']) if 'day' in ymd else None
        )

        if year and month and day:
            return (tdate.fromisoformat("{0}-{1:02d}-{2:02d}".format(
                year,
                month,
                day
            )), 3)
        elif year and month:
            return (tdate.fromisoformat("{0}-{1:02d}-{2:02d}".format(
                year,
                month,
                1
            )), 2)
        elif year:
            return (tdate.fromisoformat("{0}-{1:02d}-{2:02d}".format(
                year,
                1,
                1
            )), 1)
        else:
            return (None, 0)

    def get_individual_location(self, individual: ET.Element):
        address = individual.find('./identity/address')
        if address:
            return self.places[address.attrib['place-id']] or None

    def parse_object(self, object_: ET.Element):
        object_type = object_.attrib['object-type']
        identity = object_.find('identity')
        if not identity:
            return (None, None)

        name = None
        aliases = []
        for name_ in identity.findall('name'):
            if not name and name_.attrib['name-type'] == 'primary-name':
                name = join([
                    name_part.text or "" for name_part in name_.findall('name-part')
                ])

            if name_.attrib['name-type'] == 'alias':
                aliases.append(join([
                    name_part.text or "" for name_part in name_.findall('name_part')
                ]))

        other_info = object_.findtext('other-information')

        extra_info = {}
        extra_info['type'] = object_type

        if other_info:
            extra_info['other_info'] = other_info

        if aliases != []:
            extra_info['aliases'] = aliases

        return (name, extra_info)

    def parse_entity(self, entity: ET.Element):
        identity = entity.find('identity')
        if identity == None:
            return (None, None)

        name = None
        for name_ in identity.findall('name'):
            if name_.attrib['name-type'] == 'primary-name':
                name = join([
                    name_part.findtext('value') or "" for name_part in name_.findall('name-part')
                ])
                break

        address = identity.find('address')
        if address:
            place = self.places[address.attrib['place-id']]
            details = address.findtext('address-details')

            if details:
                address = ", ".join([details, place])
            else:
                address = place

        return (name, address)

    def get_row(self):
        self.get_places()
        self.get_programs()

        for element in self.root.findall('target'):
            program_ssid = element.attrib['sanctions-set-id'] if 'sanctions-set-id' in element.attrib else None
            program = self.programs[program_ssid] if program_ssid != None else None

            individual = element.find('individual')
            if individual != None:
                name = self.get_individual_name(individual)
                dob, accuracy = self.get_individual_dob(individual)
                location = self.get_individual_location(individual)
                yield {
                    'type': 'individual',
                    'program': program,
                    'name': name,
                    'dob': dob,
                    'dob-accuracy': accuracy,
                    'location': location,
                }
                continue

            object_ = element.find('object')
            if object_ != None:
                name, extra_info = self.parse_object(object_)
                yield {
                    'type': 'object',
                    'program': program,
                    'name': name,
                    'dob': None,
                    'location': None,
                    'extra-info': extra_info,
                }
                continue

            entity = element.find('entity')
            if entity != None:
                name, address = self.parse_entity(entity)

                yield {
                    'type': 'entity',
                    'program': program,
                    'name': name,
                    'location': address,
                    'dob': None
                }


class SDNAdvancedParser(AbstractParser):
    ns = {
        'un': 'http://www.un.org/sanctions/1.0'
    }

    def get_row(self):
        tags = set()
        for element in self.root.find('un:SanctionsEntries',  namespaces=self.ns):
            for el in element:
                tags.add(el.tag)

        yield tags


test = SDNAdvancedParser('sdn_advanced.xml')
test.parse()
