# DIMY
Hi 朋友们，这将是我们一起合作的`git repo`。

 # Notice

# 注意事项

- 在`main branch` 将会是我们共同合作的部分，或者是同步进程后的结果所以请不要直接将本地的工作直接`push`上`main`。请大家每个人都各自建立一个自己的工作分支。
- 作为初始的`repo`，我以大家的姓名的拼音缩写作为分支名字建立了以下三个：`gjw`, `csy`, `zyt`。在我们各自完成本地上的工作后可以先`push`到自己的分支上，当然各位可以创建更多的分支不过尽量标注上有意义的前缀以避免冲突，比如`gjw_workv1`之类的。
- 我们可以每周设立一个时间讨论如何合并各自的工作。讨论时间**待定**。
- 任何对于`main`上的更新，请大家自行`pull`到工作分支中。
- 每次`merge`到`main`或者更新`main`中的任何信息应当被记录在更新日志当中
- **预祝我们作业顺利！** 

# 关键日期

- 2021年4月1号
  - 期中汇报
- 2021年4月23号
  - 期末提交

# Key date
- **2021 Apr. 1** **Mid-term presentation**
- **2021 Apr. 23** **Final submission**

# 概述

- 请参照英文版

# Overview

- Platform: 

  - Raspi 4 with kali linux installed
  - Laptop/Desktop with  Linux OS installed

- Task:

  **Implement a digital contact tracing protocol - DIMY with various components and specific functionalities.**

- Requirements
  - Diffie-Hellman key exchange
  - Shamir Secret Sharing
  - Hashing
  - Bloom Filters
  - UDP/TCP socket programming

- Architecture Model

  - Client apps
    - several
    - Periodically generate **random ephemeral identifiers** for establishing a secret key in **Diffie-Hellman key exchange protocol**. This will represent the two devices that **encounter** each other.
    - After generating the ephemeral key, using **"k-out-of-n" secret sharing scheme** to produce **n secret** **shares** of the identifier. Broadcast those secret shares ~~**per minute**~~ **(10 secs)**
    - Reconstruct the the ephemeral identifier is the device stayed in the communication range for **~~at least k minutes~~ (30 secs)**
    - Use a **Daily Bloom filter (DBF)** to store the constructed encounter identifiers encounter in that ~~day~~**(10 minutes)**. Automatically **delete** encounter identifier **as soon as it has been inserted**. DBF is maintained on ~~**21-day rotation basis**~~ **(6 hrs)**. Records **Older than ~~21 days~~(1 hr) should cleaned out.**
    - Users can volunteer to upload their encounter information to the blockchain as a **combination of ~~21-day~~(6 hrs) DBFs into one Contact Bloom Filter (CBF).**
    - **Daily the Client App will query the Server** to check whether the user has met a COVID patient by **uploading a Query Bloom Filter QBF which contains the local ~~21 day~~(6 hrs) DBFs.** If the QBF is unmatched, the client app deletes it otherwise stores it separately.
  - Back-end server
    - one
    - All the records are maintained in an **immutable and decentralized** block chain.
    - Generate **authorized access token** from the block chain for the client app. Client app then can upload CBF. CBF is appended as a transcation.
    - Check if the queried QBF matched with any CBFs in the block chain. response negative if unmatched other wise matched.

- Details

  - Client App (Base)

    - Dimy.[py|c|java]

    - | Task No. | Functionality                                                |
      | -------- | ------------------------------------------------------------ |
      | 1        | Generate a **16-Byte** Ephemeral ID (EphID) after every **1 minute**. |
      | 2        | Prepare **n chunks** of the EphID by **using k-out-of-n Shamir Secret Sharing mechanism**. For this implementation, we use the values of k and n to be **3 and 6 respectively**. |
      | 3        | Broadcast these n shares @ **1 unique share per 10 seconds**. For this implementation, you **do not need to** implement the simultaneous advertisement of EphIDs proposed in the reference paper |
      | 4        | A receiver can reconstruct the advertised EphID, after it has **successfully** received **at least k shares out of the n shares being advertised**. This means that if the devices have remained in contact for **at least 30 seconds and received >= 3 shares of the same EphID**, it can **reconstruct** the EphID. **Verify** the reconstructed EphID by **taking hash** and **comparing with the hash advertised in the chunks**. |
      | 5        | The device proceeds with applying **Diffie-Hellman key exchange mechanism to arrive at the secret Encounter ID (EncID)**. |
      | 6        | A device, after **successfully constructing the EncID**, will **encode EncID into a Bloom filter** called Daily Bloom Filter (DBF), and **delete the EncID**. |
      | 7        | A DBF will store all EncIDs representing encounters faced during a **10-minute period**. **A new DBF is initiated after the 10-minute period** and each device stores **at most 6 DBFs**. DBF that is **older than 1 hour from the current time** is **deleted from the device storage**. Note that in original specifications DBF stores a day worth of EncIDs, but **for this demo we will use DBF to store EncIDs received in 10-minutes windows**. |
      | 8        | Every **60 minutes**, a device combines all of the available DBFs into another Bloom Filter called **Query Bloom Filter (QBF)**. |
      | 9        | Each device **sends this QBF to the backend server**, to check whether it has come in close contact with someone who has been diagnosed positive with COVID-19. The device will receive the result of matching performed at the back-end server. **The result is displayed to inform the user**. |
      | 10       | A user who is diagnosed positive with COVID-19, **can choose** to upload their close contacts to the backend server. **It combines all available DBF’s into a single Contact Bloom Filter (CBF)** and **uploads the CBF to the backend server.** **Once a device uploads a CBF, it stops generating the QBFs**. The device will **receive a confirmation that the upload has been successful**. |

    - Front-end should be able to configured to **DEBUG mode**
      
      - Msg sent/received, state of the Bloom Filter
    - UDP to broadcast inter device communications.
    - DBF, QBF and CBF are size of **100KB (Padding? Or maximum?)** and use **3 hashes (Hash 3 times or 3 different hash functions for each?) for encoding**.

  - Back end (Extended)

    - DimyServer.[py|c|java]

    - **Centralized instead of Blockchain Server**

    - | Task No. | Functionality                                                |
      | -------- | ------------------------------------------------------------ |
      | 11       | The back-end server stores all the received CBFs and can perform matching for each QBF received from devices. It **informs the device that has uploaded the QBF about the result** of matching, matched or not matched. If there is no CBF available, the back-end returns “**not matched**”. |

    - IP/Port can be hard coded in Client app or passed using cmd line when client app is started.
    - **Port 55000**
    - **TCP to transfer CBF/QBF**

- Presentation

  - Mid-Term

    - goup number, members name and zIDs, 
    - assignment diary that details the overall plan with assigned task for each group member, progress on the implementation and issues faced.
    - **At most 6 slides** explanation of the understanding of the DIMY protocol and presentation time slot should be divided into **each member**.
    - 5 marks (2 report + 3 presentation)
    - **Submit to Teams** 

  - Final

    - Video for the demo (Screen Recording showing the steps)
    - Detailed report of implementation
      - AssignmentReport.pdf <= **4 pages**
      - Assignment name, group number and names/IDs for all group members.
      - Executive summary that provides a brief introduction to the salient features in the assignment implementation.
      3. A brief discussion of how you have implemented the DIMY protocol. Provide a list of features that you have successfully implemented. In case you have not been able to get certain features of DIMY working, you should also mention that in your report.
      4. Discuss any design trade-offs considered and made. List what you consider is special about your implementation. Describe possible improvements and extensions to your program and indicate how you could realise them.
      5. Indicate any segments of code that you have borrowed from the Web or other books. 6. Assignment Diary: Each group is also required to attach a 1-page assignment diary to the report. This diary should maintain a weekly log of activities conducted by each group and should explicitly indicate the part played by each team member in these activities. You may use any format (Gantt chart, table, etc.) for maintaining the diary. The diary is not marked. However, if the diary is not submitted, a penalty of 2 marks will be applied. Please attach the diary at the end of the report. Do not submit it as a separate file. Unless specified otherwise, contribution from all members will be considered equal. Any difficulty in working with team members must be reported to the tutor-in-charge at the earliest.
    - Source code
    - 25 marks (Video 15 marks + (report + code) 10 marks)

  - Demo Break down

    - | Task | Segment | Description                                                  | Marks |
      | ---- | ------- | ------------------------------------------------------------ | ----- |
      | 1    | 1       | Show that 6 shares of the EphIDs are generated at each device | 0.5   |
      | 2    | 2       | Show that 6 shares of the EphIDs are generated at each device. | 1     |
      | 3    | 3-A     | Show the sending of the shares @ 1 share per 10 seconds over UDP. | 1.5   |
      |      | 3-B     | Show how the receiving of shares broadcasted by the other device. | 0.5   |
      |      | 3-C     | Show that you are keeping track of number of shares received for each EphID. | 0.5   |
      | 4    | 4-A     | Show the devices attempting re-construction of EphID when these have received at least 3 shares. | 1     |
      |      | 4-B     | Show the devices verifying the re-constructed EphID by taking the hash of re-constructed EphID and comparing with the hash value received in the advertisement. | 1     |
      | 5    | 5-A     | Show the devices computing the shared secret EncID by using DiffieHellman key exchange mechanism. | 1     |
      |      | 5-B     | Show the devices computing the shared secret EncID by using DiffieHellman key exchange mechanism. | 1     |
      | 6    | 6       | Show that the devices are encoding EncID into the DBF and deleting the EncID. | 1     |
      | 7    | 7-A     | Show that the devices are encoding multiple EncIDs into the same DBF and show the state of the DBF after each addition. | 1     |
      |      | 7-B     | Show that a new DBF gets created for the devices after every 10 minutes. A device can only store maximum of 6 DBFs. | 1     |
      | 8    | 8       | Show that after every 60 minutes, the devices combine all the available DBFs into a single QBF. | 1     |
      | 9    | 9-A     | how that the devices send the QBF to the back-end server. For extension, the back-end server is your own centralised server. | 1     |
      |      | 9-B     | Show that the devices are able to receive the result of risk analysis back from the back-end server. Show the result for a successful as well as an unsuccessful match. For extension, the back-end server is your own centralised server. | 1     |
      | 10   | 10      | Show that a device can combine the available DBF into a CBF and upload the CBF to the back-end server. For extension, the back-end server is your own centralised server. | 1     |
      | 11   | 11-A    | Show that the device is able to establish a TCP connection with the centralised server and perform Tasks 9 and 10 successfully. | 2     |
      |      | 11-B    | Show the terminal for the back-end server performing the QBF-CBF matching operation for risk analysis. |       |
      |      |         |                                                              |       |

      

- References
  - Papers
    - *DIMY.pdf*
  - Spec
    - *Assignment_2021T1_4337V1_0.pdf*

# 待做

- 制作期中汇报 (这周末完成)
  - 日记 
  - 录像

# TODO

- Mid-term report/record  (The mid-term version should be finished by this weekend)
  - Diary
    - grp ID, zid etc.
    - weekly log
    - contribution
    - challenge
    - attach to final report 
    - 1 page limitation
    - any format
  - Recording
- ~~Work break down~~
- ~~Ask Questions on Team~~

# 疑问

- **DBF, QBF, CBF大小是固定的100 KB 还是最多100 KB**
- 期中汇报的视频格式以及大小？
- ~~**日记格式，要记录些什么？**~~
  - 参考作业要求
- ~~３个哈希是指对以上三个文件使用三个不同的哈希方程还是对一个文件进行三次哈希？~~
- ~~当前端应用与后端应用沟通时我们可以自定义自己的消息传送机制嘛？比如消息的格式，大小等等。。（假如在没有实现自己的后端的情况下），另外与后端沟通的API可以自己定义嘛？~~
- ~~期中汇报需要录制视频嘛？~~
- ~~期末的视频演示需要每个组员都参与吗？~~

# Questions

- Video format & size？
- DBF, QBF and CBF are size of **100KB (Padding? Or maximum?)** and use **3 hashes (Hash 3 times or 3 different hash functions for each?) for encoding**.
- ~~Message Format for the Client App and API for communicating the Back-end.~~
- ~~Do we need to record a video for Mid term presentation?~~
- ~~Does every member in the team should participate in the Demo Video for Final?~~  
- ~~Diary format.~~

# 分工

- gjw
  - UDP 
  - k/n sharekey
  - BF module
- csy
  - ID gen module
  - DH key exchange
- zyt
  - upload CBF
  - TCP + query 

# Contribution

- gjw
  - UDP 
  - k/n sharekey
  - BF module
- csy
  - ID gen module
  - DH key exchange
- zyt
  - upload CBF
  - TCP + query

# 更新日志
- 2021 Mar.28 精简了演讲ppt，添加了每页ppt的详细描述
- 2021 Mar.27 更新了期中汇报ppt，以及疑问
- 2021 Mar.24 更新了分工，以及疑问
- 2021 Mar. 22 建立的初始工作分支，更新里主分支的`README`以及注意事项

# Change log
- 2021 Mar. 28 updated refined slides and move detials to a separate doc
- 2021 Mar. 27 updated Mid-term presentation slides and questions 
- 2021 Mar. 24 updated working assignment and questions
- 2021 Mar. 22 create initial working repo and updated the `README` in the `main` branch. 
