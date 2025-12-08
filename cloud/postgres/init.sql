CREATE EXTENSION IF NOT EXISTS pgcrypto;
create table if not exists basestations (id serial primary key, name text unique, password_salt uuid, password text);
create table if not exists users (id serial primary key, username text unique, password_salt uuid, password text);
-- create table if not exists groups (id serial primary key, name text unique);
create table if not exists users_to_basestations (user_id integer references users(id) on delete cascade, basestation_id integer references basestations(id) on delete cascade, owner boolean);
-- create table if not exists basestations_to_groups (basestation_id integer references basestations(id) on delete cascade, group_id integer references groups(id) on delete cascade);
CREATE OR REPLACE FUNCTION public.verify_user(in_username text, in_password text)          
  RETURNS boolean                                                                           
  LANGUAGE plpgsql                                                                          
 AS $function$                                                                              
 DECLARE                                                                                    
     stored_hash TEXT;                                                                      
     stored_salt UUID;                                                                      
 BEGIN                                                                                      
     SELECT password, password_salt                                                         
     INTO stored_hash, stored_salt                                                          
     FROM users                                                                             
     WHERE username = in_username;                                                          
                                                                                            
     IF NOT FOUND THEN                                                                      
         RETURN FALSE;                                                                      
     END IF;                                                                                
                                                                                            
     RETURN encode(digest(in_password || stored_salt::text, 'sha256'), 'hex') = stored_hash;
 END;                                                                                       
 $function$;

 CREATE OR REPLACE FUNCTION public.verify_basestation(in_basestation_id integer, in_password text)          
  RETURNS boolean                                                                           
  LANGUAGE plpgsql                                                                          
 AS $function$                                                                              
 DECLARE                                                                                    
     stored_hash TEXT;                                                                      
     stored_salt UUID;                                                                      
 BEGIN                                                                                      
     SELECT password, password_salt                                                         
     INTO stored_hash, stored_salt                                                          
     FROM basestations                                                                             
     WHERE id = in_basestation_id;                                                          
                                                                                            
     IF NOT FOUND THEN                                                                      
         RETURN FALSE;                                                                      
     END IF;                                                                                
                                                                                            
     RETURN encode(digest(in_password || stored_salt::text, 'sha256'), 'hex') = stored_hash;
 END;                                                                                       
 $function$;

 CREATE OR REPLACE PROCEDURE public.create_user(IN in_username text, IN in_password text)
  LANGUAGE plpgsql                                                                                                     
 AS $procedure$                                                                                                        
 DECLARE                                             
     salt UUID := gen_random_uuid();                                                                                   
 BEGIN                                                                                         
     INSERT INTO users (username, password_salt, password)                                               
     VALUES (                                                                                                          
         in_username,                                                                                                  
         salt,                                                                                                         
         encode(digest(in_password || salt::text, 'sha256'), 'hex')                                                                                                                                                 
     );                                                                                                                
 END;                                                                                                                  
 $procedure$;

  CREATE OR REPLACE PROCEDURE public.create_basestation(IN in_name text, IN in_password text)
  LANGUAGE plpgsql                                                                                                     
 AS $procedure$                                                                                                        
 DECLARE                                               
     salt UUID := gen_random_uuid();                                                                                   
 BEGIN                                                                                                                 
     INSERT INTO basestations (name, password_salt, password)                                               
     VALUES (                                                                                                          
         in_name,                                                                                                  
         salt,                                                                                                         
         encode(digest(in_password || salt::text, 'sha256'), 'hex')                                                                                                                                                 
     );                                                                                                                
 END;                                                                                                                  
 $procedure$;
-- data:
call create_user('casper', 'stdpw1234');
call create_basestation('basestation_one', 'qwerty123');
call create_basestation('based station', '420!nice');
call create_basestation('outsider base station', 'someone else');
insert into users_to_basestations(user_id, basestation_id, owner) VALUES (1, 1, TRUE);
-- insert into groups(name) VALUES ('the best group');
-- insert into users_to_groups(user_id, group_id, owner) VALUES (1, 1, TRUE);
-- insert into basestations_to_groups(basestation_id, group_id) VALUES (1, 1),(2, 1);
