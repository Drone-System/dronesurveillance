CREATE EXTENSION IF NOT EXISTS pgcrypto;
create table if not exists basestations (id serial primary key, name text, ip text);
create table if not exists users (id serial primary key, username text, password_salt uuid, password text);
create table if not exists basestations_to_users (user_id integer, basestation_id integer);
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
-- data:
call create_user('casper', 'stdpw1234');
insert into basestations (name, ip) VALUES ('localhost', '127.0.0.1'),('based station', '69.420.69.420');
