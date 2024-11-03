FROM apache/airflow:2.10.2

USER root

ARG ssh_prv_key
ARG ssh_pub_key

RUN apt-get update && \
    apt-get install -y git

# Authorize SSH Host
RUN mkdir -p /root/.ssh && \
    chmod 0700 /root/.ssh && \
    ssh-keyscan github.com > /root/.ssh/known_hosts

    
# Add the keys and set permissions
RUN echo "$ssh_prv_key" > /root/.ssh/id_rsa && \
    echo "$ssh_pub_key" > /root/.ssh/id_rsa.pub && \
    chmod 600 /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa.pub
# RUN echo "Host *" > ~/.ssh/config && echo " StrictHostKeyChecking no" >> ~/.ssh/config

USER airflow

RUN mkdir -p /home/airflow/.ssh && \
    chmod 0700 /home/airflow/.ssh 

# RUN echo "Host *" > ~/.ssh/config && echo " StrictHostKeyChecking no" >> ~/.ssh/config


    # Add the keys and set permissions
RUN echo "$ssh_prv_key" > /home/airflow/.ssh/id_rsa && \
    echo "$ssh_pub_key" > /home/airflow/.ssh/id_rsa.pub && \
    chmod 600 /home/airflow/.ssh/id_rsa && \
    chmod 600 /home/airflow/.ssh/id_rsa.pub

# RUN chown airflow:airflow /home/airflow/.ssh
# RUN chown airflow:airflow /home/airflow/
# RUN chown airflow:airflow /home/airflow/.ssh/id_rsa
# RUN chown airflow:airflow /home/airflow/.ssh/id_rsa.pub
CMD sh -c "echo 'Inside Container:' && echo 'User: $(whoami) UID: $(id -u) GID: $(id -g)'"

RUN echo 'Inside Container:' && echo 'User: $(whoami) UID: $(id -u) GID: $(id -g)'

# Install the Python dependencies
COPY requirements.txt /opt/airflow/
RUN pip install --no-cache-dir --upgrade -r /opt/airflow/requirements.txt



# COPY /dags /opt/airflow/dags
COPY /config /opt/airflow/config
COPY /plugins /opt/airflow/plugins

USER root

RUN mkdir /opt/airflow/data-version-01/
RUN chmod 777 /opt/airflow/data-version-01/
RUN cd /opt/airflow/data-version-01/ 
RUN git clone git@github.com:anazjaleel/data-version-01.git 
RUN git config --global --add safe.directory /opt/airflow/data-version-01/ 
RUN git config --global user.email "anazjbh@gmail.com"
RUN git config --global user.name "Anaz Jaleel"

RUN chmod -R 777 /opt/airflow/data-version-01
