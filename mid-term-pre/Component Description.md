# COMPONENTS Intros

## PRIVACY GENERATION COMPONENT (SIYING)

-  This component resides on the client-side as it the main approach to representing a client uniquely.

   By using a periodic random number generator along with the Diffie-Hellman key exchange algorithm (Finite cyclic groups will be used for choosing a base), we can periodically generate ephemeral identifiers as our private secret. This ephemeral ID represents the different devices or the owner of the device in the context of real life.

   The privacy generation component here provides a good mechanism for key distribution. As privacy is periodically regenerated, different devices can be distinguished and providing a good approach to distinguish groups of people who had close contact before and those who had not.

## PRIVACY SHARING COMPONENT (YUNTAO)

-  The privacy sharing component resides on the client-side as well. This component coordinates with the privacy generating component providing an approach to represent groups of people who had close contact with each other.

   To achieve this goal as well as maintain securely sharing the secret in an insecure context. The Shamir Secret Sharing algorithm is used. This is also known as “k-out-of-n sharing “. Where the secret (here is the client’s ephemeral ID) is divide into n parts in total and the only way for the other client to reconstruct the ephemeral ID is to obtain at least K parts. If client A is reconstructing client B’s ID then it means two clients will mark each other as a close contact person.

   The privacy sharing mechanism provides a good method for preventing a replay attack. To achieve integrity, the hash value of the secret can be shared as well.

   a good method for preventing a replay attack. To achieve integrity, the hash value of the secret can be shared as well.

## PRIVACY STORAGE COMPONENT (JIAWEI)

-  This component resides on both the client-side and the server-side. For efficiently and rapidly tracing the contact, fast and efficient storage, as well as the query mechanism, is necessary.

   The achieve this goal, a special data structure called Bloom Filter is being used to implement this component. Such data structure is a bit array that can efficiently determine whether a value exists or not. Although the Bloom Filter is a probabilistic data structure with false-positive property due to the collision in the hash function, parameters can be tuned to reduce the false positive probability.

   On the client-side reconstructed ephemeral IDs of other clients will be maintained as several DBF (Dayily Bloom Filter) data structure and a preconfigured amount of DBFs can be combined into a CBF(Contact Bloom Filter) for stored in the server or a QBF(Query Bloom Filter) for querying the server to be aware of close contact to a potential CONVID infector.

## Tracing System Architecture (JIAWEI)

The figure on the right shows the architecture of the entire tracing system. The client apps communicate with other client apps using UDP protocol. The privacy generating and sharing components are used for generating and sharing the ID of the client.

The privacy storage component handles the ID storage of those clients who had close contact with the current client. The data will be stored in a Bloom Filter data structure for easily uploading to or querying the server.

The server app maintains the CBF data uploaded by the client and handles the query request from the client. The communication between Client and Server is based on HTTPS on top of TCP protocol.

![sys-model](D:\MyOnedrive\OneDrive - UNSW\UNSW CS\9337_Securing_Fixed_and_Wireless_Networks\21T1\project-DIMY\mid-term-pre\sys-model.svg)

