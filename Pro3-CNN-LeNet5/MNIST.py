from tensorflow.examples.tutorials.mnist import input_data
mnist=input_data.read_data_sets("MNIST_data/",one_hot=True)

import tensorflow as tf
import numpy as np

keep_prob=tf.placeholder("float")

def weight_variable(shape):
    initial=tf.truncated_normal(shape,stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    initial=tf.constant(0.1,shape=shape)
    return tf.Variable(initial)

# convolution and pooling
def conv2d(x,W):
    return tf.nn.conv2d(x,W,strides=[1,1,1,1],padding='VALID')

def max_pool_2x2(x):
    return tf.nn.max_pool(x,ksize=[1,2,2,1],strides=[1,2,2,1],padding='VALID')

# convolution layer
def lenet5_layer(layer,weight,bias):
    W_conv=weight_variable(weight)
    b_conv=bias_variable(bias)

    h_conv=conv2d(layer,W_conv)+b_conv
    return max_pool_2x2(h_conv)

# connected layer
def dense_layer(layer,weight,bias):
    W_fc=weight_variable(weight)
    b_fc=bias_variable(bias)

    return tf.matmul(layer,W_fc)+b_fc

def main():
    sess=tf.InteractiveSession()
    # input layer
    x=tf.placeholder("float",shape=[None,784])
    y_=tf.placeholder("float",shape=[None,10])

    # first layer
    x_image=tf.pad(tf.reshape(x,[-1,28,28,1]),[[0,0],[2,2],[2,2],[0,0]])
    layer=lenet5_layer(x_image,[5,5,1,6],[6])

    # second layer
    layer=lenet5_layer(layer,[5,5,6,16],[16])

    # third layer
    W_conv3=weight_variable([5,5,16,120])
    b_conv3=bias_variable([120])

    layer=conv2d(layer,W_conv3)+b_conv3
    layer=tf.reshape(layer,[-1,120])

    # all connected layer
    con_layer=dense_layer(layer,[120,84],[84])

    # output
    con_layer=dense_layer(con_layer,[84,10],[10])
    y_conv=tf.nn.softmax(tf.nn.dropout(con_layer,keep_prob))

    # train and evalute
    cross_entropy=tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_,logits=y_conv))
    train_step=tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
    correct_prediction=tf.equal(tf.argmax(y_conv,1),tf.argmax(y_,1))
    accuracy=tf.reduce_mean(tf.cast(correct_prediction,"float"))
    sess.run(tf.global_variables_initializer())
    for i in range(30000):
        batch=mnist.train.next_batch(50)
        if i%100==0:
            train_accuracy=accuracy.eval(feed_dict={
                x:batch[0],y_:batch[1],keep_prob:1.0
            })
            print("step %d,training accuracy %g"%(i,train_accuracy))
        train_step.run(feed_dict={x:batch[0],y_:batch[1],keep_prob:0.5})

    print("Test accuracy %g"%accuracy.eval(feed_dict={
        x:mnist.test.images,y_:mnist.test.labels,keep_prob:1.0
    }))

if __name__=='__main__':
    main()