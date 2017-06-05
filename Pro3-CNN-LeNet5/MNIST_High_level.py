import tensorflow as tf
import numpy as np
from tensorflow.contrib import learn,layers,framework
from tensorflow.examples.tutorials.mnist import input_data
sess=tf.InteractiveSession()
INPUT_IMAGE_SIZE=28

# convolution and pooling
def lenet5_layer(tensor,n_filters,kernel_size,pool_size,activation_fn=None,padding='VALID'):
    conv=layers.conv2d(tensor,
        num_outputs=n_filters,
        kernel_size=kernel_size,
        activation_fn=activation_fn,
        padding=padding)
    pool=tf.nn.max_pool(conv,ksize=pool_size,strides=[1,2,2,1],padding=padding)
    return pool

# dense connected layer
def dense_layer(tensor_in,layers_list,activation_fn=None,keep_prob=None):
    tensor_out=tensor_in
    for i in range(len(layers_list)):
        layer=layers_list[i]
        if i==len(layers_list)-1:
            activation_fn=tf.nn.softmax
        tensor_out=layers.fully_connected(tensor_out,layer,activation_fn=activation_fn)
        tensor_out=layers.dropout(tensor_out,keep_prob=keep_prob)
    return tensor_out
        

def lenet5_model(X,y,mode,image_size=(-1,INPUT_IMAGE_SIZE,INPUT_IMAGE_SIZE,1),pool_size=(1,2,2,1)):
    X=tf.pad(tf.reshape(X,image_size),[[0,0],[2,2],[2,2],[0,0]],mode="CONSTANT")
    print("x ",X.shape)
    print("y ",y.shape)

    layer1=lenet5_layer(X,6,[5,5],pool_size)
    print("layer1 ",layer1.shape)
    layer2=lenet5_layer(layer1,16,[5,5],pool_size)
    print("layer2 ",layer2.shape)
    layer3=layers.conv2d(layer2,num_outputs=120,kernel_size=[5,5],activation_fn=tf.nn.softmax,padding='VALID')
    print("layer3 ",layer3.shape)
    result=dense_layer(layer3,[84,10],keep_prob=0.5)
    result=tf.reshape(result,[-1,10])
    print("result ",result.shape)
    prediction,loss=learn.models.logistic_regression_zero_init(result,y)
    train_op=layers.optimize_loss(loss,framework.get_global_step(),optimizer='Adagrad',learning_rate=0.1)
    return prediction,loss,train_op

def main():
    # read mnist data
    mnist=input_data.read_data_sets("MNIST_data/",one_hot=True)
    num=mnist.train.images.shape[0]
    print("num ",num)
    classifier=learn.Estimator(model_fn=lenet5_model,model_dir='./logs')

    classifier.fit(mnist.train.images,mnist.train.labels,steps=20000,batch_size=50)
    prediction=np.array(list(classifier.predict(mnist.test.images)))
    print("prediction ",prediction.shape)
    correct_pred=tf.equal(tf.argmax(prediction,1),tf.argmax(mnist.test.labels,1))
    accuracy=tf.reduce_mean(tf.cast(correct_pred,tf.float32))
    print("accuracy ",tf.InteractiveSession().run(accuracy))
    # accuracy=metrics.accuracy_score(mnist.test.labels,prediction)
    # accuracy=classifier.evaluate(x=test_images,y=mnist.test.labels,steps=1)
    # print("accuracy ",accuracy)
    # print('Accuracy: ',accuracy)

if __name__=='__main__':
    main()