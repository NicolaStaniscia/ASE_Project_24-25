# Unire i file al progetto e aggiungere nel compose (per effettuare l'analisi delle performance) questo:

locust_user:
    build: ./locust_user
    container_name: locust_user
    restart: on-failure
    ports:
      - 8089:8089
    environment:
      - JWT_PASSWORD=JwtGACHA2425
    networks:
      - user_net
    develop:  # Questa parte opzionale (utile in fase di test)
      watch:
        - action: rebuild
          path: ./locust_user
          target: /app
  
  locust_admin:
    build: ./locust_admin
    container_name: locust_admin
    restart: on-failure
    ports:
      - 8090:8090
    environment:
      - JWT_PASSWORD=JwtGACHA2425
    networks:
      - admin_net
    develop:  # Questa parte opzionale (utile in fase di test)
      watch:
        - action: rebuild
          path: ./locust_admin
          target: /app
