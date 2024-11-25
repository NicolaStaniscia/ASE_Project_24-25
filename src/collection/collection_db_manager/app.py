from flask import Flask, request, make_response, jsonify 
from os import getenv
import pymysql


class MyApp(Flask):

    def __init__(self, name):
        super().__init__(name)

        # Add GET endpoints
        self.add_url_rule('/users', 'get_all_users', self.get_all_owners, methods=['GET'])
        self.add_url_rule('/gacha', 'get_system_gachas', self.retrieve_system_gachas, methods=['GET'])
        self.add_url_rule('/gacha/<int:gacha_id>', 'get_gacha_info', self.get_gacha_info, methods=['GET'])
        self.add_url_rule('/user_collection/<int:user_id>', 'get_user_collection', self.get_user_collection, methods=['GET'])  # Also for admin
        self.add_url_rule('/user_collection/<int:user_id>/grouped', 'get_user_collection_(grouped_mode)', self.get_grouped_user_collection, methods=['GET'])

        # Edit endpoints
        self.add_url_rule('/edit/user_collection', 'add_gacha_to_a_collection', self.add_gacha_to_collection, methods=['POST'])  # Used also for assign gacha during a roll
        self.add_url_rule('/edit/user_collection', 'edit_a_gacha_of_a_collection', self.edit_gacha_collection, methods=['PATCH'])
        self.add_url_rule('/edit/user_collection/<int:id_own>', 'remove_gacha_from_a_collection', self.delete_gatcha_from_collection, methods=['DELETE'])
        self.add_url_rule('/edit_gacha', 'add_system_gacha', self.add_system_gacha, methods=['POST'])
        self.add_url_rule('/edit_gacha', 'edit_info_of_a_system_gacha', self.edit_gacha, methods=['PATCH'])
        self.add_url_rule('/edit_gacha/<int:gacha_id>', 'delete_a_system_gacha', self.delete_system_gacha, methods=['DELETE'])
        

    # ! FUNCTIONS

    # * Connect to db
    def connect_db(self):
        config = {
            'host': getenv('MYSQL_HOST'),
            'user': getenv('MYSQL_USER'),
            'password': getenv('MYSQL_PASSWORD'),
            'database': getenv('MYSQL_DATABASE')
        }

        try:
            # Connect to db
            conn = pymysql.connect(**config)
            return conn
        except pymysql.MySQLError as e:
            raise Exception(f'Error during DB connection: {str(e)}')
        

    # * Serialize json to send as response
    # ! Without this function, json doesn't have keys
    def serialize_response(self, cursor, item_list: list):
        # Retrieve col names
        column_names = [desc[0] for desc in cursor.description]
        # Convert each row in a dict
        return [dict(zip(column_names, item)) for item in item_list]
    

    # ! EDIT ENDPOINTS

    # * Delete a system gacha
    def delete_system_gacha(self, gacha_id):

        try:
            # Check data
            if not gacha_id:
                return make_response(jsonify(error='Gacha ID missing'), 400)

            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'DELETE FROM Gacha WHERE id = %s'
            cursor = conn.cursor()

            # Execute query
            cursor.execute(query, (gacha_id,))
            conn.commit()

            return make_response(jsonify(result=f'Gacha (id: {gacha_id}) deleted from the system'), 200)
        except Exception as e:
            if conn:
                conn.rollback()

            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # * Add a system gacha
    def add_system_gacha(self):

        def is_valid_json(data):
            if not data: return False

            required_keys = {'name', 'extractionProb', 'rarity', 'image', 'damage', 'speed', 'critical', 'accuracy'}

            if isinstance(data, list):
                # Check all items in the list
                for item in data:
                    if not isinstance(item, dict) or not required_keys.issubset(item.keys()):
                        return False
            elif isinstance(data, dict):
                # Check a single dictionary
                if not required_keys.issubset(data.keys()):
                    return False
            else:
                # Invalid format (not list or dict)
                return False
            
            return True

        # Retrieve data
        data = request.get_json()

        try:
            if not is_valid_json(data):
                return make_response(jsonify(error='Invalid or missing data in JSON'), 400)
            
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = '''INSERT INTO Gacha (name, extractionProb, rarity, image, 
                    damage, speed, critical, accuracy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
            cursor = conn.cursor()

            n = 0
            if isinstance(data, list):    
                # Add each element
                for item in data:
                    cursor.execute(query, tuple(item.values()))
                    conn.commit()
                    n += 1
            else:
                # Add single element
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                n += 1

            return make_response(jsonify(result=f'Added {n} new gachas'), 200)
            
        except Exception as e:
            if conn:
                conn.rollback()
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # * Edit info of a gacha
    def edit_gacha(self):

        def retrieve_data(): # Function to retrieve a standard format of JSON data
            data = request.get_json()
            
            # List of column and values
            column = []
            values = []

            if 'name' in data:
                column.append('name = %s')
                values.append(data['name'])
            if 'extractionProb' in data:
                column.append('extractionProb = %s')
                values.append(data['extractionProb'])
            if 'image' in data:
                column.append('image = %s')
                values.append(data['image'])
            if 'class' in data:
                column.append('class = %s')
                values.append(data['class'])
            if 'damage' in data:
                column.append('damage = %s')
                values.append(data['damage'])
            if 'speed' in data:
                column.append('speed = %s')
                values.append(data['speed'])
            if 'critical' in data:
                column.append('critical = %s')
                values.append(data['critical'])
            if 'accuracy' in data:
                column.append('accuracy = %s')
                values.append(data['accuracy'])

            # Add Gacha id
            values.append(data['id'])

            return (column, values)
        
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Retrieve data
            column, values = retrieve_data() 
            if not column or not values:
                return make_response(jsonify(error='No valid column to update'), 400)
            
            # Query
            query = f'UPDATE Gacha SET {', '.join(column)} WHERE id = %s'
            cursor = conn.cursor()

            # Execute
            cursor.execute(query, tuple(values))
            conn.commit()

            return make_response(jsonify(result=f'Gacha (id: {values[-1]}) updated'), 200)
        
        except Exception as e:
            if conn:
                conn.rollback()

            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

        
    # * Edit a gacha in a collection
    def edit_gacha_collection(self):
        def retrieve_data():
            data = request.get_json()
            column = []
            values = []
            
            if 'user_id' in data:
                column.append('user = %s')
                values.append(data['user_id'])
            if 'gacha_id' in data:
                column.append('gacha = %s')
                values.append(data['gacha_id'])
            if 'in_auction' in data:
                column.append('in_auction = %s')
                values.append(data['in_auction'])

            values.append(data['id'])

            return (column, values)

        try:
            column, values = retrieve_data()
            if not column or not values:
                return make_response(jsonify(error='Invalid parameters'), 400)
            
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = f'UPDATE Owned SET {', '.join(column)} WHERE id = %s'
            cursor = conn.cursor()

            # Execute
            cursor.execute(query, tuple(values))
            conn.commit()

            return make_response(jsonify(result=f'Row n. {values[-1]} updated'), 200)

        except Exception as e:
            if conn:
                conn.rollback()
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # * Add a gacha to a specific colletion
    def add_gacha_to_collection(self):
        # Retrieve data
        data = request.get_json()
        
        try:
            if not data or ('user_id' not in data) or ('gacha_id' not in data):
                return make_response(jsonify(error='Invalid parameters'), 400)

            user_id = data['user_id']
            gacha_id = data['gacha_id']

            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'INSERT INTO Owned (user, gacha) VALUES (%s, %s)'
            cursor = conn.cursor()

            # Execute
            cursor.execute(query, (user_id, gacha_id))
            conn.commit()

            return make_response(jsonify(result=f"Gacha {gacha_id} added to user (id: {user_id}) collection"), 200)

        except Exception as e:
            if conn:
                conn.rollback()

            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # * Delete a gacha from a specific colletion
    def delete_gatcha_from_collection(self, id_own):
        try:
            
            if not id_own:
                return make_response(jsonify(error='ID Own missing'), 400)

            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'DELETE FROM Owned WHERE id = %s'
            cursor = conn.cursor()

            # Execute
            cursor.execute(query, (id_own,))
            conn.commit()

            return make_response(jsonify(result=f"Row (id: {id_own}) deleted"), 200)

        except Exception as e:
            if conn:
                conn.rollback()
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # ! GET ENDPOINTS    

    # * See all user
    def get_all_owners(self):
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'SELECT DISTINCT(user) FROM Owned'
            cursor = conn.cursor()
            
            # Execute
            cursor.execute(query)
            result = cursor.fetchall()

            users = self.serialize_response(cursor, result)

            return make_response(users, 200)
        
        except Exception as e:
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    # * See gacha info
    def get_gacha_info(self, gacha_id):
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'SELECT * FROM Gacha WHERE id = %s'
            cursor = conn.cursor()

            # Execute
            cursor.execute(query, (gacha_id,))
            result = cursor.fetchall()

            gacha = self.serialize_response(cursor, result)[0]

            return make_response(gacha, 200)
        except Exception as e:
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

        
    # * Retrieve user collection (grouped)
    def get_grouped_user_collection(self, user_id):
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = ''' SELECT G.id, name, image, rarity, count(*) as quantity
                FROM Owned O
                JOIN Gacha G ON O.gacha = G.id
                WHERE O.user = %s
                GROUP BY G.id, name, image, rarity
            '''
            cursor = conn.cursor()

            # Execute query
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            gachas = self.serialize_response(cursor, results)

            return make_response(gachas, 200)
        
        except Exception as e:
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    
    # * Retrieve user collection
    def get_user_collection(self, user_id):
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Query
            query = 'SELECT O.id as idOwn, G.id as gachaId, name, image, rarity FROM Owned O, Gacha G WHERE O.gacha = G.id AND user = %s'
            cursor = conn.cursor()

            # Execute query
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            gachas = self.serialize_response(cursor, results)

            return make_response(gachas, 200)
        
        except Exception as e:
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
        

    # * Retrieve all system gachas
    def retrieve_system_gachas(self):
        cursor = None
        conn = None
        
        try:
            conn = self.connect_db()
            if not conn:
                return make_response(jsonify(error='DB error'), 500)
            
            # Create a cursor to execute a query
            cursor = conn.cursor()
            
            # Execute the query and retrieve all rows
            cursor.execute('SELECT id, name, image, rarity, extractionProb FROM Gacha')
            results = cursor.fetchall()
            gachas = self.serialize_response(cursor, results)

            return make_response(gachas, 200)

        
        except Exception as e:
            return make_response(jsonify(error=str(e)), 500)
        
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    
app = MyApp(__name__)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
