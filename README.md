————————————————————————————————————
Reidentification project Algorithm
============  
### 실행 방법  
  1. algorithm 1A && algorithm 1B  
    만일 알고리즘 1A와 1B만을 실행하고 싶다면 python 3으로 실행하면 된다. 실행에 사용되는 csv파일은 파일 내 소스를 통하여 수정할 수 있다. 실행에 필요한 module은 requirement에 적혀있다.  

    > example  
    python3 1A.py  

  1. GUI version
    GUI는 현재 algorithm 1B를 이용하여 구현하였다. 실제 실행은 start.py를 이용하여 이루어진다.  
    현재 파일 읽어오기, 알고리즘 수행, 결과 출력, 결과 저장이 구현되어 있으며 알고리즘 개선에 따라 발전될 사항이 있다.

    > example  
    python3 start.py
    

### 동작 순서  
  1. setting input files   
    input file은 비교할 두 파일과 database에 대한 metadata 이다.  

    * database = released Database = 비식별화된 DB를 의미  
    * aux_array = AUX = 공격자가 입수할 수 있는 정보  
       
    1. 비교할 두 input file format  
      다음과 같은 형식으로 들어온다. 또한 두 input file의 attribute는 동일하도록 미리 손봐둔다.  
                
      record(index) 	|attribute #1	|att #2 |att #3  
      --------- 		|------------	|------ |------
      record #1(No.1) 	|value        |value  |value 
      record #2 		|value        |value  |value 
      record #3 		|value        |value  |value 

    1. metadata format
      metadata는 database에 대한 속성을 설명하는 파일이다. database의 속성 순서대로 작성한다.  
      속성의 예로는 index, string, number, number_range(ex. 100~200), date(2015-01-01) 등이 있다.  
                
      > [example]  
      index  
      string  
      number  
      string  
      date  


  1. scoring  (include similarity function)  
    입력받은 두 database에서 각각의 record를 모두 비교한다. (즉 N by M)  
    알고리즘 수행결과로 N by M의 2차원 유사도 배열이 나오게 된다.  
    각 record를 비교하는 방법(sim 함수) 알고리즘의 성능이 달려있다.  
    (다만 모든 algorithm이 공통속성만을 비교)  
    
    * 유사도 측정 방법  

    > algorithm 1A  
    algorithm 1A에서는 각 속성값마다의 유사도를 측정한다.  
    이후 속성 값 사이의 유사도 중에서 최소 유사도를 두 record 간의 유사도로 정의한다.  

    ```python  
    for record_d in releaseD:
      for record_aux in AUX:
        for attribute in 공통속성:
          유사도 = sim(record_aux, record_aux)
          if 최소값 > 유사도:
            최소값 = 유사도
            output[record_d][record_aux] = 유사도
    ```  
    > algorithm 1B  
    algorithm 1B에서는 각 속성값마다의 유사도를 측정한다.  
    이 때, 단순히 유사도를 구하는 것이 아니라 해당 속성에서 해당 값이 차지하고 있는 비율을 이용한다.  
    예를 들어 남, 여 비율이 6:4인 성별 속성에 대해서 값을 구한다고 하자. 만일 후보가 성별 '여'로 일치한다면, 유사도 1을 가지는 것이 아니라 (1 - 0.4[속성 차지 비율]) * 1 을 값으로 가지게 된다.  
    위 과정을 모든 속성에 대해서 수행한 후, 유사도를 모두 더하면 그 값이 해당 후보가 가지는 유사도가 된다.  

    ```python  
    for record_d in releaseD:
      for record_aux in AUX:
        for attribute in 공통속성:
          유사도 += (1-p(x)) * sim(record_aux, record_aux)
      output[record_d][record_aux] = 유사도
    ```  

    * 속성별 유사도 측정 방법

      1. index  
        index는 단순히 행을 구별하기 위한 수단에 불과하다. 실제 database에는 없는 정보로 사용자가 임의로 집어넣은 정보이므로 따로 비교하지 않는다.  

      1. string  
        Levenshtein 알고리즘을 이용하여 문자열 간의 유사도를 구한다.  

      1. number  
        두 수간의 차이가 작을수록 유사도가 높다고 해석한다. 따라서 다음과 같이 식을 구성할 수 있다.  
        1 - (|aux - record| / record)  

      1. number_range  
        해당 수가 수 범위 내의 들어가있는지를 판별한다.  

      1. date  
        두 날짜 사이의 간격을 구한다. 만일 정확히 일치한다면 유사도 1을 부여하고, 그 차이가 7일 이내라면 0.5의 유사도를 부여한다. 차이가 7일보다 많이 난다면 유사도 0을 부여한다.  


  1. matching set  
    scoring에서 구한 N by M 2차원 배열을 입력으로 받아 releaseD의 각 record에 대해서 (후보, 확률)을 뽑아낸다.  
    
    > algorithm 1A  
    algorithm 1A에서는 일정한 상수값 alpha보다 높은 유사도를 가진 후보만을 취급한다.  

    ```python  
    for row in input_arrayM:
      for col in input_arrayM:
        if input_arrayM[row][col] >= alpha:
          output_dict_arrayR[row][col] = input_arrayM[row][col]
    ```

    > algorithm 1B  
    algorithm 1B에서는 첫 번째 후보와 두 번째 후보 사이에 유의미한 차이(eccentricity)가 있을 경우 해당 값을 후보로 취한다.  
    현재는 편의상 이유로 최대 5개의 후보를 뽑게 하고 있다.  

    ```python  
    for row in input_arrayM:
      maximum = max(input_arrayM)
      sec_max = second_max(input_arrayM)
      if maximum - sec_max >= eccentricity:
        output_dict_arrayR[row][index of maximum] = maximum
    ```    
    
  + 참고자료
  robust De-anonymization of Lage Datasets (How to Break Anonymity of the Netflix Prize Dataset), Arvind Narayanan and Vitaly Shmatikov, February 5, 2008  
=======  
